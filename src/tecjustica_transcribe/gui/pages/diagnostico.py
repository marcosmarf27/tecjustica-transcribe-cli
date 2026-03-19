"""Página de diagnóstico — verificações do sistema estilo terminal."""

from __future__ import annotations

from nicegui import ui

from tecjustica_transcribe.core.checks import executar_todas_verificacoes


def conteudo() -> None:
    """Renderiza a página de diagnóstico do sistema."""

    with ui.row().classes("w-full items-center q-mb-md"):
        ui.icon("monitor_heart").classes("text-2xl").style("color: var(--accent)")
        ui.label("SISTEMA").classes("vsc-section").style(
            "font-size: 13px !important; margin-bottom: 0 !important"
        )

    container = ui.column().classes("w-full")

    def verificar() -> None:
        container.clear()
        resultados = executar_todas_verificacoes()

        with container:
            with ui.card().classes("vsc-panel w-full"):
                ui.label("VERIFICAÇÕES").classes("vsc-section")

                for r in resultados:
                    with ui.row().classes("vsc-row items-center gap-3"):
                        if r.ok:
                            ui.icon("check_circle", size="16px").classes(
                                "check-ok"
                            )
                        else:
                            ui.icon("cancel", size="16px").classes("check-fail")

                        ui.label(r.nome).style(
                            "font-size: 13px; font-weight: 500; min-width: 160px"
                        )
                        ui.label(r.detalhe).classes("mono").style(
                            "font-size: 12px; color: var(--text-dim)"
                        )

            # Resumo
            falhas = [r for r in resultados if not r.ok]
            with ui.row().classes("items-center gap-2 q-mt-md"):
                if not falhas:
                    ui.icon("check_circle", size="18px").classes("check-ok")
                    ui.label("Tudo pronto para transcrever").style(
                        "font-size: 13px; color: var(--success)"
                    )
                else:
                    ui.icon("warning", size="18px").classes("check-warn")
                    ui.label(
                        f"{len(falhas)} problema(s) encontrado(s)"
                    ).style("font-size: 13px; color: var(--warning)")

    verificar()

    ui.button(
        "Re-verificar", icon="refresh", on_click=verificar
    ).classes("vsc-btn-flat q-mt-md")
