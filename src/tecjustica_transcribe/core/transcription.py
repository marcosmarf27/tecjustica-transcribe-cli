"""Pipeline de transcrição WhisperX — lógica pura sem UI."""

from __future__ import annotations

import gc
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ProgressCallback = Callable[[str, str], None]


@dataclass
class TranscriptionConfig:
    arquivo: Path
    output_dir: Path = Path("./transcricoes")
    diarizacao: bool = True
    modelo: str = "large-v2"
    idioma: str = "pt"
    batch_size: int | None = None  # None = auto


@dataclass
class TranscriptionResult:
    segments: list[dict]
    caminho_srt: Path
    caminho_txt: Path
    caminho_json: Path


def _obter_batch_size() -> int:
    """Ajusta batch_size automaticamente baseado na VRAM."""
    import torch

    if not torch.cuda.is_available():
        return 4
    vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    if vram_gb >= 10:
        return 16
    if vram_gb >= 6:
        return 8
    return 4


def _formatar_timestamp_srt(segundos: float) -> str:
    """Converte segundos para formato SRT: HH:MM:SS,mmm"""
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = int(segundos % 60)
    ms = int((segundos % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _salvar_srt(segments: list[dict], caminho: Path) -> None:
    """Gera arquivo .srt com timestamps e falantes."""
    linhas: list[str] = []
    for i, seg in enumerate(segments, 1):
        inicio = _formatar_timestamp_srt(seg["start"])
        fim = _formatar_timestamp_srt(seg["end"])
        falante = seg.get("speaker", "")
        texto = seg.get("text", "").strip()
        prefixo = f"[{falante}] " if falante else ""
        linhas.append(f"{i}")
        linhas.append(f"{inicio} --> {fim}")
        linhas.append(f"{prefixo}{texto}")
        linhas.append("")
    caminho.write_text("\n".join(linhas), encoding="utf-8")


def _salvar_txt(segments: list[dict], caminho: Path) -> None:
    """Gera arquivo .txt com texto puro e identificação de falantes."""
    linhas: list[str] = []
    falante_atual = ""
    for seg in segments:
        falante = seg.get("speaker", "")
        texto = seg.get("text", "").strip()
        if falante and falante != falante_atual:
            falante_atual = falante
            linhas.append(f"\n[{falante}]")
        linhas.append(texto)
    caminho.write_text("\n".join(linhas).strip(), encoding="utf-8")


def _salvar_json(segments: list[dict], caminho: Path) -> None:
    """Gera arquivo .json com dados completos."""
    dados = {
        "segments": segments,
        "total_segments": len(segments),
    }
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def executar_pipeline(
    config: TranscriptionConfig,
    hf_token: str | None = None,
    on_progress: ProgressCallback | None = None,
) -> TranscriptionResult:
    """Executa o pipeline completo de transcrição WhisperX.

    Args:
        config: Configuração da transcrição.
        hf_token: Token HuggingFace para diarização.
        on_progress: Callback (etapa, mensagem) para reportar progresso.

    Returns:
        TranscriptionResult com segmentos e caminhos dos arquivos gerados.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        RuntimeError: Se ocorrer OOM ou outro erro de runtime.
        ValueError: Se diarização solicitada sem token HF.
    """

    def _progress(etapa: str, msg: str) -> None:
        if on_progress:
            on_progress(etapa, msg)

    if not config.arquivo.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {config.arquivo}")

    import torch
    import whisperx

    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    batch_size = config.batch_size or _obter_batch_size()

    def _liberar_vram(*refs: object) -> None:
        """Deleta referências e libera VRAM."""
        for ref in refs:
            del ref
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    try:
        # 1. Carregar modelo
        _progress("modelo", "Carregando modelo WhisperX...")
        model = whisperx.load_model(
            config.modelo,
            device=device,
            compute_type=compute_type,
            language=config.idioma,
        )
        _progress("modelo", "Modelo carregado")

        # 2. Carregar áudio
        _progress("audio", "Carregando áudio...")
        audio = whisperx.load_audio(str(config.arquivo))
        _progress("audio", "Áudio carregado")

        # 3. Transcrever
        _progress("transcricao", f"Transcrevendo (batch_size={batch_size})...")
        result = model.transcribe(audio, batch_size=batch_size)
        _progress("transcricao", "Transcrição concluída")

        # Liberar modelo whisper — não é mais necessário
        _liberar_vram(model)
        model = None  # noqa: F841

        # 4. Alinhar timestamps
        _progress("alinhamento", "Alinhando timestamps...")
        model_a, metadata = whisperx.load_align_model(
            language_code=config.idioma, device=device
        )
        result = whisperx.align(
            result["segments"], model_a, metadata, audio, device=device
        )
        _progress("alinhamento", "Timestamps alinhados")

        # Liberar modelo de alinhamento
        _liberar_vram(model_a)
        model_a = None  # noqa: F841

        # 5. Diarizar (se solicitado)
        if config.diarizacao:
            if not hf_token:
                raise ValueError(
                    "Token HuggingFace necessário para diarização. "
                    "Configure com 'tecjustica-transcribe init' ou desabilite diarização."
                )
            _progress("diarizacao", "Identificando falantes...")
            from whisperx.diarize import DiarizationPipeline

            diarize_model = DiarizationPipeline(token=hf_token, device=device)
            diarize_segments = diarize_model(audio)
            result = whisperx.assign_word_speakers(diarize_segments, result)
            _progress("diarizacao", "Falantes identificados")

            # Liberar modelo de diarização
            _liberar_vram(diarize_model)
            diarize_model = None  # noqa: F841

        segments = (
            result.get("segments", result) if isinstance(result, dict) else result
        )

        # 6. Salvar arquivos
        config.output_dir.mkdir(parents=True, exist_ok=True)
        nome_base = config.arquivo.stem

        caminho_srt = config.output_dir / f"{nome_base}.srt"
        caminho_txt = config.output_dir / f"{nome_base}.txt"
        caminho_json = config.output_dir / f"{nome_base}.json"

        _progress("salvando", "Salvando arquivos...")
        _salvar_srt(segments, caminho_srt)
        _salvar_txt(segments, caminho_txt)
        _salvar_json(segments, caminho_json)
        _progress("salvando", "Arquivos salvos")

        return TranscriptionResult(
            segments=segments,
            caminho_srt=caminho_srt,
            caminho_txt=caminho_txt,
            caminho_json=caminho_json,
        )
    finally:
        # Limpeza final garantida — mesmo em caso de erro
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
