"""Página de configurações — token HF, pasta padrão, GPU/CPU."""

from __future__ import annotations

from nicegui import ui

from tecjustica_transcribe.core.config import (
    CONFIG_FILE,
    carregar_config,
    salvar_config,
    salvar_token_hf,
)


def conteudo() -> None:
    """Renderiza a página de configurações."""
    config = carregar_config()

    with ui.row().classes("w-full items-center q-mb-md"):
        ui.icon("tune").classes("text-2xl").style("color: var(--accent)")
        ui.label("CONFIGURAÇÕES").classes("vsc-section").style(
            "font-size: 13px !important; margin-bottom: 0 !important"
        )

    # ---- Token HuggingFace ----
    with ui.card().classes("vsc-panel w-full q-mb-sm"):
        ui.label("HUGGINGFACE TOKEN").classes("vsc-section")
        ui.label(
            "Necessário para diarização (identificação de falantes)."
        ).style("font-size: 12px; color: var(--text-dim); margin-bottom: 8px")

        token_input = ui.input(
            label="Token",
            value=config.get("hf_token", ""),
            password=True,
            password_toggle_button=True,
        ).classes("vsc-input mono w-full")

        def salvar_token() -> None:
            token = token_input.value.strip()
            if token:
                salvar_token_hf(token)
                ui.notify("Token salvo!", type="positive")
            else:
                ui.notify("Token vazio", type="warning")

        with ui.row().classes("items-center gap-3 q-mt-sm"):
            ui.button("Salvar token", icon="save", on_click=salvar_token).classes(
                "vsc-btn"
            )
            ui.link(
                "Obter token",
                "https://huggingface.co/settings/tokens",
                new_tab=True,
            ).style("font-size: 12px")

        ui.label(
            "Aceite os termos: huggingface.co/pyannote/speaker-diarization-3.1"
        ).style("font-size: 11px; color: var(--text-dim); margin-top: 8px")

    # ---- Preferências ----
    with ui.card().classes("vsc-panel w-full q-mb-sm"):
        ui.label("TRANSCRIÇÃO").classes("vsc-section")

        output_input = ui.input(
            label="Pasta de saída padrão",
            value=config.get("output_dir", "./transcricoes"),
        ).classes("vsc-input mono w-full")

        with ui.row().classes("items-end gap-4 q-mt-sm"):
            device_select = ui.select(
                options=["auto", "cuda", "cpu"],
                value=config.get("device", "auto"),
                label="Dispositivo",
            ).classes("vsc-select").style("min-width: 120px")

            batch_input = ui.number(
                label="Batch size (0 = auto)",
                value=config.get("batch_size", 0),
                min=0,
                max=32,
            ).classes("vsc-input").style("min-width: 160px")

        def salvar_preferencias() -> None:
            cfg = carregar_config()
            cfg["output_dir"] = output_input.value
            cfg["device"] = device_select.value
            cfg["batch_size"] = int(batch_input.value or 0)
            salvar_config(cfg)
            ui.notify("Configurações salvas!", type="positive")

        ui.button(
            "Salvar preferências", icon="save", on_click=salvar_preferencias
        ).classes("vsc-btn q-mt-md")

    # ---- Info ----
    with ui.card().classes("vsc-panel w-full"):
        ui.label("ARQUIVO DE CONFIGURAÇÃO").classes("vsc-section")
        ui.label(str(CONFIG_FILE)).classes("mono").style(
            "font-size: 11px; color: var(--text-dim)"
        )
