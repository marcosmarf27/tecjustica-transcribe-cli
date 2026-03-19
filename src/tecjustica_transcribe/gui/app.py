"""Entry point da GUI — layout VS Code-like com activity bar."""

from __future__ import annotations

from typing import Callable

from tecjustica_transcribe import __version__

VSCODE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {
    --bg: #1e1e1e;
    --sidebar: #252526;
    --activitybar: #333333;
    --titlebar: #323233;
    --statusbar: #007acc;
    --border: #3c3c3c;
    --text: #cccccc;
    --text-dim: #858585;
    --accent: #0e639c;
    --accent-hover: #1177bb;
    --input-bg: #3c3c3c;
    --card-bg: #252526;
    --hover: #2a2d2e;
    --success: #4ec9b0;
    --error: #f44747;
    --warning: #cca700;
}

body, .q-page, .q-page-container {
    background-color: var(--bg) !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif !important;
    color: var(--text) !important;
}

/* ---- Title bar ---- */
.titlebar {
    background-color: var(--titlebar) !important;
    border-bottom: 1px solid var(--border) !important;
    min-height: 36px !important;
    padding: 0 16px !important;
}

.titlebar .q-toolbar__title {
    font-size: 13px !important;
    font-weight: 400 !important;
    opacity: 0.8;
}

/* ---- Activity bar ---- */
.activitybar {
    background-color: var(--activitybar) !important;
    border-right: 1px solid var(--border) !important;
}

.activitybar .q-item {
    padding: 0 !important;
    min-height: 48px !important;
}

.sidebar-item {
    width: 100% !important;
    height: 38px !important;
    min-height: 38px !important;
    border-radius: 0 !important;
    opacity: 0.5;
    transition: opacity 0.15s ease, background-color 0.15s ease;
    border-left: 2px solid transparent !important;
    padding: 0 12px !important;
    margin: 0 !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    letter-spacing: 0 !important;
    justify-content: flex-start !important;
    color: var(--text) !important;
}

.sidebar-item .q-icon {
    font-size: 18px !important;
    margin-right: 10px !important;
}

.sidebar-item:hover {
    opacity: 0.85;
    background-color: var(--hover) !important;
}

.sidebar-item.active {
    opacity: 1 !important;
    border-left-color: var(--accent) !important;
    background-color: rgba(255,255,255,0.04) !important;
}

/* ---- Status bar ---- */
.statusbar {
    background-color: var(--statusbar) !important;
    min-height: 24px !important;
    max-height: 24px !important;
    padding: 0 10px !important;
}

.statusbar * {
    font-size: 12px !important;
    line-height: 24px !important;
}

/* ---- Panels (cards) ---- */
.vsc-panel {
    background-color: var(--card-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    color: var(--text) !important;
}

.vsc-panel .q-card__section {
    padding: 12px 16px !important;
}

/* ---- Section headers ---- */
.vsc-section {
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 1.2px !important;
    color: var(--text-dim) !important;
    font-weight: 600 !important;
    margin-bottom: 8px !important;
    user-select: none;
}

/* ---- Input fields ---- */
.vsc-input .q-field__control {
    background-color: var(--input-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    color: var(--text) !important;
    padding: 0 8px !important;
    min-height: 28px !important;
}

.vsc-input .q-field__control:focus-within {
    border-color: var(--accent) !important;
    outline: 1px solid var(--accent) !important;
}

.vsc-input .q-field__label {
    color: var(--text-dim) !important;
    font-size: 12px !important;
}

.vsc-input .q-field__native,
.vsc-input .q-field__prefix,
.vsc-input .q-field__suffix {
    color: var(--text) !important;
}

.vsc-input .q-field__bottom {
    display: none !important;
}

/* ---- Select fields ---- */
.vsc-select .q-field__control {
    background-color: var(--input-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    min-height: 28px !important;
}

.vsc-select .q-field__native,
.vsc-select .q-select__dropdown-icon {
    color: var(--text) !important;
}

/* ---- Primary button ---- */
.vsc-btn {
    background-color: var(--accent) !important;
    color: white !important;
    border-radius: 2px !important;
    text-transform: none !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    letter-spacing: 0 !important;
    padding: 4px 14px !important;
    min-height: 30px !important;
    box-shadow: none !important;
}

.vsc-btn:hover {
    background-color: var(--accent-hover) !important;
}

.vsc-btn:disabled {
    opacity: 0.4 !important;
}

/* ---- Secondary/flat button ---- */
.vsc-btn-flat {
    background-color: transparent !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    text-transform: none !important;
    font-size: 12px !important;
    letter-spacing: 0 !important;
    min-height: 26px !important;
    box-shadow: none !important;
}

.vsc-btn-flat:hover {
    background-color: var(--hover) !important;
}

/* ---- Danger button ---- */
.vsc-btn-danger {
    background-color: transparent !important;
    color: var(--error) !important;
    border: 1px solid var(--error) !important;
    border-radius: 2px !important;
    text-transform: none !important;
    font-size: 12px !important;
    box-shadow: none !important;
}

.vsc-btn-danger:hover {
    background-color: rgba(244, 71, 71, 0.1) !important;
}

/* ---- Monospace ---- */
.mono {
    font-family: 'JetBrains Mono', Consolas, 'Courier New', monospace !important;
    font-size: 13px !important;
}

/* ---- Progress bar ---- */
.vsc-progress .q-linear-progress__track {
    background-color: var(--border) !important;
    opacity: 1 !important;
}

.vsc-progress .q-linear-progress__model {
    background-color: var(--statusbar) !important;
}

/* ---- Switch ---- */
.vsc-switch .q-toggle__inner--truthy .q-toggle__track {
    background-color: var(--accent) !important;
    opacity: 1 !important;
}

.vsc-switch .q-toggle__label {
    color: var(--text) !important;
    font-size: 13px !important;
}

/* ---- Upload area ---- */
.vsc-upload .q-uploader {
    background-color: var(--card-bg) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 0 !important;
    color: var(--text-dim) !important;
    max-height: 80px !important;
}

.vsc-upload .q-uploader__header {
    background-color: transparent !important;
}

/* ---- Check icons ---- */
.check-ok { color: var(--success) !important; }
.check-fail { color: var(--error) !important; }
.check-warn { color: var(--warning) !important; }

/* ---- Links ---- */
a, .q-btn--flat.text-primary {
    color: #3794ff !important;
}

/* ---- Expansion panel ---- */
.q-expansion-item .q-item {
    color: var(--text-dim) !important;
}

/* ---- Dialog ---- */
.q-dialog .q-card {
    background-color: var(--sidebar) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
}

/* ---- Table rows ---- */
.vsc-row {
    padding: 6px 12px;
    border-bottom: 1px solid var(--border);
    transition: background-color 0.1s;
}

.vsc-row:hover {
    background-color: var(--hover);
}

/* ---- Scrollbar ---- */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background-color: rgba(121,121,121,0.4); }
::-webkit-scrollbar-thumb:hover { background-color: rgba(121,121,121,0.7); }

/* ---- Notification ---- */
.q-notification {
    font-size: 13px !important;
    border-radius: 0 !important;
}
"""


def _obter_info_sistema() -> str:
    """Retorna string com info GPU/CUDA para a barra de status."""
    try:
        import torch

        if torch.cuda.is_available():
            gpu = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            cuda = torch.version.cuda
            return f"$(gpu_icon) {gpu} ({vram:.1f} GB)  |  CUDA {cuda}"
        return "CPU (sem GPU CUDA)"
    except ImportError:
        return "PyTorch não instalado"


# Cache do info do sistema (evita import pesado a cada navegação)
_system_info: str | None = None


def _get_system_info() -> str:
    global _system_info
    if _system_info is None:
        _system_info = _obter_info_sistema()
    return _system_info


def _layout(pagina_ativa: str, conteudo_fn: Callable[[], None]) -> None:
    """Layout VS Code: title bar + activity bar + content + status bar."""
    from nicegui import ui

    ui.dark_mode(True)
    ui.add_css(VSCODE_CSS)

    menu_items = [
        ("Transcrever", "/", "mic"),
        ("Modelos", "/modelos", "inventory_2"),
        ("Configurações", "/configuracoes", "tune"),
        ("Sistema", "/diagnostico", "monitor_heart"),
    ]

    # ---- Title bar ----
    with ui.header().classes("titlebar items-center"):
        ui.icon("gavel").classes("text-lg").style("opacity: 0.6")
        ui.label("TecJustiça Transcribe").style(
            "font-size: 13px; opacity: 0.7; margin-left: 8px"
        )

    # ---- Sidebar ----
    with ui.left_drawer(value=True).props(
        "width=180 persistent no-swipe-open no-swipe-close"
    ).classes("activitybar"):
        with ui.column().classes("w-full gap-0 q-pt-xs"):
            for label, path, icon in menu_items:
                is_active = label == pagina_ativa
                btn = ui.button(
                    label,
                    icon=icon,
                    on_click=lambda p=path: ui.navigate.to(p),
                )
                btn.props("flat dense unelevated align=left no-caps").classes(
                    f"sidebar-item {'active' if is_active else ''}"
                )

    # ---- Main content ----
    with ui.column().classes("w-full max-w-4xl mx-auto").style(
        "padding: 20px 24px"
    ):
        conteudo_fn()

    # ---- Status bar ----
    with ui.footer().classes("statusbar"):
        with ui.row().classes("w-full items-center justify-between"):
            info = _get_system_info()
            # Replace placeholder with icon
            ui.label(info.replace("$(gpu_icon)", "")).style(
                "font-size: 12px; font-family: inherit"
            )
            ui.label(f"v{__version__}").style("font-size: 12px; opacity: 0.8")


def main() -> None:
    """Inicia a GUI desktop."""
    from nicegui import ui

    from tecjustica_transcribe.gui.pages import (
        configuracoes,
        diagnostico,
        modelos,
        transcricao,
    )

    @ui.page("/")
    def page_transcricao():
        _layout("Transcrever", transcricao.conteudo)

    @ui.page("/modelos")
    def page_modelos():
        _layout("Modelos", modelos.conteudo)

    @ui.page("/configuracoes")
    def page_configuracoes():
        _layout("Configurações", configuracoes.conteudo)

    @ui.page("/diagnostico")
    def page_diagnostico():
        _layout("Sistema", diagnostico.conteudo)

    # WSL2: pywebview falha silenciosamente mesmo com DISPLAY (WSLg).
    # Usar browser que funciona sempre. Linux nativo → janela desktop.
    import platform

    native = False
    if platform.system() == "Linux" and "microsoft" not in platform.release().lower():
        try:
            import webview  # noqa: F401

            native = True
        except ImportError:
            pass

    ui.run(
        title="TecJustiça Transcribe",
        native=native,
        window_size=(1050, 750),
        reload=False,
        show=not native,
    )
