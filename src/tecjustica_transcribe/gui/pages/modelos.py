"""Página de gerenciamento de modelos — download/exclusão."""

from __future__ import annotations

import queue
import threading

from nicegui import ui

from tecjustica_transcribe.core.models import (
    baixar_modelo,
    deletar_modelo,
    listar_modelos,
)

_progress_queue: queue.Queue = queue.Queue()


def conteudo() -> None:
    """Renderiza a página de modelos."""

    with ui.row().classes("w-full items-center q-mb-md"):
        ui.icon("inventory_2").classes("text-2xl").style("color: var(--accent)")
        ui.label("MODELOS").classes("vsc-section").style(
            "font-size: 13px !important; margin-bottom: 0 !important"
        )

    ui.label("Modelos WhisperX em ~/.cache/huggingface/hub/").classes(
        "mono"
    ).style("font-size: 11px; color: var(--text-dim); margin-bottom: 12px")

    container = ui.column().classes("w-full gap-1")

    def refresh() -> None:
        container.clear()
        modelos = listar_modelos()
        with container:
            for m in modelos:
                with ui.row().classes(
                    "vsc-row w-full items-center justify-between"
                ):
                    with ui.row().classes("items-center gap-3"):
                        if m.downloaded:
                            ui.icon("check_circle", size="18px").classes(
                                "check-ok"
                            )
                        else:
                            ui.icon("cloud_download", size="18px").style(
                                "color: var(--text-dim)"
                            )

                        with ui.column().classes("gap-0"):
                            ui.label(m.name).classes("mono").style(
                                "font-size: 13px; font-weight: 500"
                            )
                            tamanho = (
                                f"{m.size_mb / 1000:.1f} GB"
                                if m.size_mb >= 1000
                                else f"{m.size_mb} MB"
                            )
                            status = "Baixado" if m.downloaded else "Não baixado"
                            ui.label(f"~{tamanho}  ·  {status}").style(
                                "font-size: 11px; color: var(--text-dim)"
                            )

                    if m.downloaded:
                        ui.button(
                            "Excluir",
                            icon="delete_outline",
                            on_click=lambda n=m.name: confirmar_exclusao(n),
                        ).classes("vsc-btn-danger")
                    else:
                        ui.button(
                            "Baixar",
                            icon="download",
                            on_click=lambda n=m.name: download(n),
                        ).classes("vsc-btn-flat")

    def confirmar_exclusao(name: str) -> None:
        with ui.dialog() as dialog, ui.card().classes("vsc-panel"):
            ui.label(f"Excluir modelo {name}?").style(
                "font-weight: 500; font-size: 14px"
            )
            ui.label("O modelo será removido do cache local.").style(
                "font-size: 12px; color: var(--text-dim)"
            )
            with ui.row().classes("w-full justify-end gap-2 q-mt-md"):
                ui.button("Cancelar", on_click=dialog.close).classes(
                    "vsc-btn-flat"
                )
                ui.button(
                    "Excluir",
                    icon="delete_outline",
                    on_click=lambda: excluir(name, dialog),
                ).classes("vsc-btn-danger")
        dialog.open()

    def excluir(name: str, dialog: object) -> None:
        deletar_modelo(name)
        dialog.close()  # type: ignore[attr-defined]
        refresh()
        ui.notify(f"Modelo {name} excluído", type="info")

    def download(name: str) -> None:
        ui.notify(f"Baixando {name}... Isso pode demorar.", type="info")

        def run() -> None:
            try:
                baixar_modelo(
                    name,
                    on_progress=lambda msg: _progress_queue.put(("info", msg)),
                )
                _progress_queue.put(("done", name))
            except Exception as e:
                _progress_queue.put(("error", str(e)))

        threading.Thread(target=run, daemon=True).start()

    def check_progress() -> None:
        while not _progress_queue.empty():
            try:
                item = _progress_queue.get_nowait()
            except queue.Empty:
                break
            if item[0] == "done":
                ui.notify(f"Modelo {item[1]} baixado!", type="positive")
                refresh()
            elif item[0] == "error":
                ui.notify(f"Erro: {item[1]}", type="negative")

    ui.timer(1.0, check_progress)
    refresh()
