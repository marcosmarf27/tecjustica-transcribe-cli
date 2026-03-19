"""Página de transcrição — seleção de arquivo + progresso + resultado."""

from __future__ import annotations

import os
import platform
import queue
import subprocess
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path

from nicegui import events, ui

from tecjustica_transcribe.core.config import obter_token_hf
from tecjustica_transcribe.core.transcription import (
    TranscriptionConfig,
    TranscriptionResult,
    executar_pipeline,
)

ETAPAS_PROGRESSO = {
    "modelo": 0.10,
    "audio": 0.25,
    "transcricao": 0.50,
    "alinhamento": 0.70,
    "diarizacao": 0.90,
    "salvando": 1.00,
}

ETAPAS_LABELS = {
    "modelo": "Carregando modelo",
    "audio": "Processando áudio",
    "transcricao": "Transcrevendo",
    "alinhamento": "Alinhando timestamps",
    "diarizacao": "Identificando falantes",
    "salvando": "Salvando arquivos",
}


@dataclass
class _EstadoTranscricao:
    """Estado global que persiste entre navegações de página."""

    transcrevendo: bool = False
    progresso_valor: float = 0.0
    progresso_msg: str = ""
    progresso_etapa: str = ""
    resultado: TranscriptionResult | None = None
    erro: str | None = None
    arquivo: str = ""
    modelo: str = "large-v2"
    output_dir: str = "./transcricoes"
    diarizacao: bool = True
    fila: queue.Queue = field(default_factory=queue.Queue)

    def resetar(self) -> None:
        self.transcrevendo = True
        self.progresso_valor = 0.0
        self.progresso_msg = "Iniciando..."
        self.progresso_etapa = ""
        self.resultado = None
        self.erro = None
        while not self.fila.empty():
            try:
                self.fila.get_nowait()
            except queue.Empty:
                break


_estado = _EstadoTranscricao()

def _abrir_no_sistema(caminho: Path) -> None:
    """Abre arquivo ou pasta com o aplicativo padrão do SO."""
    try:
        if not caminho.exists():
            ui.notify(f"Não encontrado: {caminho}", type="negative")
            return
        sistema = platform.system()
        if sistema == "Windows":
            os.startfile(str(caminho))  # type: ignore[attr-defined]
        elif sistema == "Darwin":
            subprocess.Popen(["open", str(caminho)])
        else:
            subprocess.Popen(["xdg-open", str(caminho)])
    except Exception as exc:
        ui.notify(f"Erro ao abrir: {exc}", type="negative")


def _formatar_timestamp(segundos: float) -> str:
    """Formata segundos como MM:SS ou H:MM:SS."""
    s = int(segundos)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def conteudo() -> None:
    """Renderiza a página de transcrição."""

    # ---- Header ----
    with ui.row().classes("w-full items-center q-mb-md"):
        ui.icon("mic").classes("text-2xl").style("color: var(--accent)")
        ui.label("TRANSCREVER").classes("vsc-section").style(
            "font-size: 13px !important; margin-bottom: 0 !important"
        )

    # ---- Arquivo ----
    with ui.card().classes("vsc-panel w-full q-mb-sm"):
        ui.label("ARQUIVO").classes("vsc-section")

        caminho_input = ui.input(
            label="Caminho do arquivo",
            placeholder="/mnt/c/Users/.../audiencia.mp4",
            value=_estado.arquivo,
            on_change=lambda e: setattr(_estado, "arquivo", e.value),
        ).classes("vsc-input mono w-full")

        async def on_upload(e: events.UploadEventArguments) -> None:
            try:
                temp_dir = Path(tempfile.gettempdir()) / "tecjustica"
                temp_dir.mkdir(exist_ok=True)
                dest = temp_dir / e.file.name
                dest.write_bytes(await e.file.read())
                path = str(dest)
                _estado.arquivo = path
                caminho_input.set_value(path)
                ui.notify(f"Arquivo carregado: {e.file.name}", type="positive")
            except Exception as exc:
                ui.notify(f"Erro ao salvar arquivo: {exc}", type="negative")

        with ui.element("div").classes("vsc-upload w-full q-mt-xs"):
            ui.upload(
                label="Arrastar arquivo aqui",
                on_upload=on_upload,
                auto_upload=True,
            ).props(
                'accept=".mp4,.wav,.mp3,.m4a,.ogg,.flac" '
                "max-file-size=524288000 flat bordered"
            ).classes("w-full")

    # ---- Opções ----
    with ui.card().classes("vsc-panel w-full q-mb-sm"):
        ui.label("OPÇÕES").classes("vsc-section")

        with ui.row().classes("w-full items-end gap-4"):
            output_input = ui.input(
                label="Pasta de saída",
                value=_estado.output_dir,
                on_change=lambda e: setattr(_estado, "output_dir", e.value),
            ).classes("vsc-input mono flex-1")

            modelo_select = ui.select(
                options=["large-v2", "medium", "small", "tiny"],
                value=_estado.modelo,
                label="Modelo",
                on_change=lambda e: setattr(_estado, "modelo", e.value),
            ).classes("vsc-select").style("min-width: 140px")

        with ui.element("div").classes("vsc-switch q-mt-sm"):
            diarizacao_switch = ui.switch(
                "Identificar falantes (diarização)",
                value=_estado.diarizacao,
                on_change=lambda e: setattr(_estado, "diarizacao", e.value),
            )

    # ---- Botão transcrever ----
    def transcrever() -> None:
        arquivo = caminho_input.value.strip() or _estado.arquivo
        _estado.arquivo = arquivo
        if not arquivo:
            ui.notify("Selecione um arquivo", type="warning")
            return

        if not Path(arquivo).exists():
            ui.notify(f"Arquivo não encontrado: {arquivo}", type="negative")
            return

        token: str | None = None
        if diarizacao_switch.value:
            token = obter_token_hf()
            if not token:
                ui.notify(
                    "Token HuggingFace não configurado. Vá em Configurações.",
                    type="negative",
                )
                return

        _estado.resetar()
        btn_transcrever.disable()
        progresso_panel.visible = True
        resultado_panel.visible = False
        download_panel.visible = False
        transcricao_panel.visible = False
        erro_label.visible = False
        progresso_bar.value = 0
        progresso_label.text = "Iniciando..."
        # Limpar etapas visuais
        for el in etapa_elements.values():
            el.style("opacity: 0.3")

        config = TranscriptionConfig(
            arquivo=Path(arquivo),
            output_dir=Path(output_input.value),
            diarizacao=diarizacao_switch.value,
            modelo=modelo_select.value,
        )

        def run() -> None:
            try:
                result = executar_pipeline(
                    config,
                    hf_token=token,
                    on_progress=lambda etapa, msg: _estado.fila.put(
                        ("progress", etapa, msg)
                    ),
                )
                _estado.fila.put(("done", result))
            except Exception as e:
                _estado.fila.put(("error", str(e)))

        threading.Thread(target=run, daemon=True).start()

    btn_transcrever = ui.button(
        "Transcrever", icon="play_arrow", on_click=transcrever
    ).classes("vsc-btn q-mt-sm")

    if _estado.transcrevendo:
        btn_transcrever.disable()

    # ---- Progresso ----
    progresso_panel = ui.card().classes("vsc-panel w-full q-mt-sm")
    progresso_panel.visible = _estado.transcrevendo or (
        _estado.resultado is not None and _estado.erro is None
    )

    etapa_elements: dict[str, object] = {}

    with progresso_panel:
        ui.label("PROGRESSO").classes("vsc-section")

        progresso_bar = ui.linear_progress(
            value=_estado.progresso_valor, show_value=False
        ).classes("vsc-progress w-full")

        progresso_label = ui.label(
            _estado.progresso_msg or "Iniciando..."
        ).classes("mono").style("font-size: 12px; color: var(--text-dim); margin-top: 8px")

        # Etapas visuais
        with ui.column().classes("w-full gap-0 q-mt-sm"):
            for etapa_key, etapa_label in ETAPAS_LABELS.items():
                with ui.row().classes("items-center gap-2").style(
                    "padding: 3px 0"
                ) as row:
                    done = (
                        ETAPAS_PROGRESSO.get(etapa_key, 0)
                        <= _estado.progresso_valor
                        and _estado.progresso_valor > 0
                    )
                    is_current = _estado.progresso_etapa == etapa_key
                    if done:
                        ui.icon("check", size="16px").classes("check-ok")
                    elif is_current:
                        ui.spinner(size="16px").style("color: var(--accent)")
                    else:
                        ui.icon("radio_button_unchecked", size="16px").style(
                            "color: var(--border)"
                        )
                    ui.label(etapa_label).style("font-size: 12px")

                opacity = "1" if done or is_current else "0.3"
                row.style(f"opacity: {opacity}")
                etapa_elements[etapa_key] = row

    # ---- Resultado ----
    resultado_panel = ui.card().classes("vsc-panel w-full q-mt-sm")
    resultado_panel.visible = _estado.resultado is not None

    with resultado_panel:
        with ui.row().classes("items-center gap-2"):
            ui.icon("check_circle", size="20px").classes("check-ok")
            ui.label("CONCLUÍDO").classes("vsc-section").style(
                "margin-bottom: 0 !important; color: var(--success) !important"
            )

        resultado_texto = ""
        if _estado.resultado:
            r = _estado.resultado
            resultado_texto = (
                f"{r.caminho_txt.parent}/\n"
                f"  {r.caminho_txt.name}   (texto puro)\n"
                f"  {r.caminho_srt.name}   (legendas SRT)\n"
                f"  {r.caminho_json.name}  (dados completos)"
            )
        resultado_label = ui.label(resultado_texto).classes("mono").style(
            "white-space: pre; font-size: 12px; margin-top: 8px; "
            "color: var(--text); line-height: 1.6"
        )

    # ---- Downloads ----
    download_panel = ui.card().classes("vsc-panel w-full q-mt-sm")
    download_panel.visible = False

    # ---- Transcrição (somente leitura) ----
    transcricao_panel = ui.card().classes("vsc-panel w-full q-mt-sm")
    transcricao_panel.visible = False

    def _popular_resultado(result: TranscriptionResult) -> None:
        """Popula downloads e transcrição somente-leitura."""
        # Downloads
        download_panel.visible = True
        download_panel.clear()
        with download_panel:
            with ui.row().classes("items-center gap-2"):
                ui.icon("download", size="20px").style(
                    "color: var(--accent)"
                )
                ui.label("ARQUIVOS").classes("vsc-section").style(
                    "margin-bottom: 0 !important"
                )
            with ui.row().classes("gap-2 q-mt-sm"):
                for caminho, label, icone in [
                    (result.caminho_txt, "TXT", "description"),
                    (result.caminho_srt, "SRT", "subtitles"),
                    (result.caminho_json, "JSON", "code"),
                ]:
                    ui.button(
                        label,
                        icon=icone,
                        on_click=lambda p=caminho: _abrir_no_sistema(p),
                    ).classes("vsc-btn")
                ui.button(
                    "Abrir pasta",
                    icon="folder_open",
                    on_click=lambda: _abrir_no_sistema(
                        result.caminho_txt.parent
                    ),
                ).classes("vsc-btn-flat")

        # Transcrição (somente leitura)
        transcricao_panel.visible = True
        transcricao_panel.clear()
        with transcricao_panel:
            with ui.row().classes("items-center gap-2"):
                ui.icon("subject", size="20px").style(
                    "color: var(--accent)"
                )
                ui.label("TRANSCRIÇÃO").classes("vsc-section").style(
                    "margin-bottom: 0 !important"
                )

            with ui.scroll_area().style("max-height: 400px"):
                for seg in result.segments:
                    start = seg.get("start", 0)
                    speaker = seg.get("speaker", "")
                    text = seg.get("text", "").strip()

                    with ui.row().classes(
                        "segment-row items-center w-full gap-2"
                    ).style("padding: 6px 8px"):
                        ui.label(
                            _formatar_timestamp(start)
                        ).classes("mono").style(
                            "color: var(--accent); font-size: 12px; "
                            "min-width: 50px"
                        )
                        if speaker:
                            ui.label(speaker).classes("mono").style(
                                "font-size: 11px; "
                                "background: var(--input-bg); "
                                "padding: 1px 6px; "
                                "border-radius: 2px; "
                                "color: var(--text-dim)"
                            )
                        ui.label(text).style("font-size: 13px")

    # Restaurar se já houver resultado (navegação entre páginas)
    if _estado.resultado is not None:
        _popular_resultado(_estado.resultado)

    # ---- Erro ----
    erro_label = ui.label(
        f"Erro: {_estado.erro}" if _estado.erro else ""
    ).classes("mono").style(
        "color: var(--error); font-size: 12px; margin-top: 8px"
    )
    erro_label.visible = _estado.erro is not None

    # ---- Timer para fila de progresso ----
    def check_progress() -> None:
        while not _estado.fila.empty():
            try:
                item = _estado.fila.get_nowait()
            except queue.Empty:
                break

            if item[0] == "progress":
                _, etapa, msg = item
                _estado.progresso_msg = msg
                _estado.progresso_etapa = etapa
                progresso_label.text = msg
                if etapa in ETAPAS_PROGRESSO:
                    _estado.progresso_valor = ETAPAS_PROGRESSO[etapa]
                    progresso_bar.value = ETAPAS_PROGRESSO[etapa]
                # Atualizar etapas visuais
                for ek, el in etapa_elements.items():
                    if ETAPAS_PROGRESSO.get(ek, 0) <= _estado.progresso_valor:
                        el.style("opacity: 1")

            elif item[0] == "done":
                result: TranscriptionResult = item[1]
                _estado.transcrevendo = False
                _estado.resultado = result
                _estado.progresso_msg = "Concluído!"
                _estado.progresso_valor = 1.0
                btn_transcrever.enable()
                progresso_label.text = "Concluído!"
                progresso_bar.value = 1.0
                resultado_panel.visible = True
                for el in etapa_elements.values():
                    el.style("opacity: 1")
                resultado_label.text = (
                    f"{result.caminho_txt.parent}/\n"
                    f"  {result.caminho_txt.name}   (texto puro)\n"
                    f"  {result.caminho_srt.name}   (legendas SRT)\n"
                    f"  {result.caminho_json.name}  (dados completos)"
                )
                ui.notify("Transcrição concluída!", type="positive")
                _popular_resultado(result)

            elif item[0] == "error":
                error_msg = item[1]
                _estado.transcrevendo = False
                _estado.erro = error_msg
                btn_transcrever.enable()
                progresso_panel.visible = False
                erro_label.text = f"Erro: {error_msg}"
                erro_label.visible = True
                ui.notify(f"Erro: {error_msg}", type="negative")

    ui.timer(0.5, check_progress)
