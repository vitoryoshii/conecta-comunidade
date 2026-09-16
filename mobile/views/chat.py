"""Tela 8 — Chat (com card de entrega agendada)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

import flet as ft

from mobile import theme as t
from mobile.components.comuns import cabecalho

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

CORES_STATUS_ENTREGA = {
    "agendada": t.VERDE_PRIMARIO,
    "realizada": t.AZUL_INSTITUCIONAL,
    "cancelada": t.URGENCIA,
}


def _bolha(mensagem: dict[str, Any], sou_eu: bool) -> ft.Row:
    """Bolha de mensagem alinhada conforme o remetente."""
    # A API grava e devolve em UTC; aqui convertemos para o fuso do aparelho,
    # senão a bolha mostraria um horário deslocado.
    horario = ""
    try:
        momento = datetime.fromisoformat(mensagem["criada_em"])
        if momento.tzinfo is None:
            momento = momento.replace(tzinfo=timezone.utc)
        horario = momento.astimezone().strftime("%H:%M")
    except (KeyError, ValueError):
        pass

    balao = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    mensagem.get("texto", ""),
                    size=13,
                    color=t.BRANCO if sou_eu else t.AZUL_INSTITUCIONAL,
                ),
                ft.Text(
                    horario,
                    size=9,
                    color="#CDEBD9" if sou_eu else t.TEXTO_SECUNDARIO,
                    text_align=ft.TextAlign.RIGHT,
                ),
            ],
            spacing=3,
            tight=True,
        ),
        padding=ft.Padding.symmetric(horizontal=12, vertical=9),
        bgcolor=t.VERDE_PRIMARIO if sou_eu else t.BRANCO,
        border_radius=ft.BorderRadius(
            top_left=14,
            top_right=14,
            bottom_left=14 if sou_eu else 2,
            bottom_right=2 if sou_eu else 14,
        ),
        border=None if sou_eu else ft.Border.all(1, t.BORDA),
        width=250,
    )

    return ft.Row(
        [balao],
        alignment=ft.MainAxisAlignment.END if sou_eu else ft.MainAxisAlignment.START,
    )


def _card_entrega(app: App, entrega: dict[str, Any]) -> ft.Container:
    """Card destacado com o encontro combinado."""
    status = entrega.get("status", "agendada")
    cor = CORES_STATUS_ENTREGA.get(status, t.VERDE_PRIMARIO)

    def concluir(_: ft.ControlEvent) -> None:
        """Marca a entrega como realizada e fecha o pedido."""
        if app.executar(
            lambda: app.api.atualizar_entrega(entrega["id"], {"status": "realizada"}),
            "Entrega confirmada. Obrigado por ajudar!",
        ):
            app.renderizar()

    def cancelar(_: ft.ControlEvent) -> None:
        """Cancela o agendamento mantendo o histórico."""
        if app.executar(
            lambda: app.api.atualizar_entrega(entrega["id"], {"status": "cancelada"}),
            "Entrega cancelada.",
        ):
            app.renderizar()

    acoes: list[ft.Control] = []
    if status == "agendada":
        acoes = [
            ft.TextButton(
                content="Marcar como realizada",
                icon=t.ICONES["sucesso"],
                on_click=concluir,
                style=ft.ButtonStyle(color=t.VERDE_ESCURO),
            ),
            ft.TextButton(
                content="Cancelar",
                on_click=cancelar,
                style=ft.ButtonStyle(color=t.URGENCIA),
            ),
        ]

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(t.ICONES["agenda"], size=18, color=cor),
                        ft.Text(
                            "Entrega agendada",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=t.AZUL_INSTITUCIONAL,
                            expand=True,
                        ),
                        t.etiqueta(status.capitalize(), cor_texto=t.BRANCO, cor_fundo=cor),
                    ],
                    spacing=8,
                ),
                ft.Row(
                    [
                        ft.Icon(t.ICONES["data"], size=13, color=t.TEXTO_SECUNDARIO),
                        ft.Text(
                            f"{entrega.get('data', '')} às {entrega.get('hora', '')}",
                            size=12,
                            color=t.TEXTO_SECUNDARIO,
                        ),
                    ],
                    spacing=6,
                ),
                ft.Row(
                    [
                        ft.Icon(t.ICONES["local"], size=13, color=t.TEXTO_SECUNDARIO),
                        ft.Text(
                            entrega.get("local") or "Local a combinar",
                            size=12,
                            color=t.TEXTO_SECUNDARIO,
                            expand=True,
                        ),
                    ],
                    spacing=6,
                ),
                ft.Row(acoes, spacing=0) if acoes else ft.Container(height=0),
            ],
            spacing=6,
        ),
        padding=14,
        bgcolor=t.VERDE_SUAVE,
        border_radius=t.RAIO,
        border=ft.Border.all(1, cor),
    )


def _dialogo_agendamento(app: App, solicitacao_id: int) -> None:
    """Abre o formulário de agendamento de entrega."""
    amanha = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
    campo_data = t.campo("Data", valor=amanha, icone=t.ICONES["data"])
    campo_hora = t.campo("Hora", valor="14:00", icone=t.ICONES["horario"])
    campo_local = t.campo("Local do encontro", icone=t.ICONES["local"])

    dialogo = ft.AlertDialog(
        modal=True,
        title=ft.Text("Agendar entrega", color=t.AZUL_INSTITUCIONAL),
        content=ft.Column([campo_data, campo_hora, campo_local], spacing=10, height=230),
    )

    def fechar(_: ft.ControlEvent) -> None:
        """Fecha o diálogo sem salvar."""
        app.page.pop_dialog()

    def salvar(_: ft.ControlEvent) -> None:
        """Cria a entrega e recarrega o chat com o card visível."""
        if not campo_data.value or not campo_hora.value:
            app.aviso("Informe data e hora.", erro=True)
            return

        criada = app.executar(
            lambda: app.api.criar_entrega(
                {
                    "solicitacao_id": solicitacao_id,
                    "data": campo_data.value,
                    "hora": campo_hora.value,
                    "local": campo_local.value or "",
                }
            ),
            "Entrega agendada!",
        )
        app.page.pop_dialog()
        if criada is not None:
            app.renderizar()

    dialogo.actions = [
        ft.TextButton(content="Cancelar", on_click=fechar),
        ft.FilledButton(content="Agendar", on_click=salvar, bgcolor=t.VERDE_PRIMARIO),
    ]
    app.page.show_dialog(dialogo)


def construir(app: App) -> ft.Control:
    """Monta o chat: card de entrega, histórico e campo de envio."""
    parametros = app.state.rota_atual.parametros
    com: int = parametros.get("com")
    nome: str = parametros.get("nome", "Conversa")
    solicitacao_id: int | None = parametros.get("solicitacao_id")
    solicitacao_titulo: str | None = parametros.get("solicitacao_titulo")

    mensagens = app.executar(lambda: app.api.listar_mensagens(com)) or []

    # Busca a entrega vinculada ao pedido desta conversa, se houver.
    entrega: dict[str, Any] | None = None
    if solicitacao_id is not None:
        entregas = app.executar(lambda: app.api.listar_entregas(solicitacao_id=solicitacao_id)) or []
        entrega = entregas[0] if entregas else None

    campo_texto = ft.TextField(
        hint_text="Escreva uma mensagem...",
        filled=True,
        fill_color=t.BRANCO,
        border_radius=24,
        border_color=t.BORDA,
        focused_border_color=t.VERDE_PRIMARIO,
        color=t.AZUL_INSTITUCIONAL,
        content_padding=ft.Padding.symmetric(horizontal=16, vertical=12),
        expand=True,
        multiline=False,
    )

    def enviar(_: ft.ControlEvent) -> None:
        """Envia a mensagem digitada e recarrega a conversa."""
        texto = (campo_texto.value or "").strip()
        if not texto:
            return
        if app.executar(lambda: app.api.enviar_mensagem(com, texto, solicitacao_id)) is None:
            return
        campo_texto.value = ""
        app.renderizar()

    campo_texto.on_submit = enviar

    # --- Corpo da conversa ------------------------------------------------
    itens: list[ft.Control] = []
    if entrega is not None:
        itens.append(_card_entrega(app, entrega))
    if solicitacao_titulo:
        itens.append(
            t.cartao(
                ft.Row(
                    [
                        ft.Icon(t.ICONES["doacoes"], size=16, color=t.VERDE_PRIMARIO),
                        ft.Text(
                            f"Conversa sobre: {solicitacao_titulo}",
                            size=12,
                            color=t.TEXTO_SECUNDARIO,
                            expand=True,
                        ),
                    ],
                    spacing=8,
                ),
                padding=10,
            )
        )

    if mensagens:
        itens += [
            _bolha(mensagem, mensagem.get("remetente_id") == app.state.usuario_id)
            for mensagem in mensagens
        ]
    else:
        itens.append(t.area_vazia("Nenhuma mensagem ainda.\nDiga um oi!", t.ICONES["conversa"]))

    acoes_cabecalho: list[ft.Control] = []
    if solicitacao_id is not None and entrega is None:
        acoes_cabecalho.append(
            ft.IconButton(
                t.ICONES["agenda"],
                icon_color=t.VERDE_PRIMARIO,
                tooltip="Agendar entrega",
                on_click=lambda _: _dialogo_agendamento(app, solicitacao_id),
            )
        )

    return ft.Column(
        [
            cabecalho(nome, app.voltar, acoes_cabecalho, "online no Conecta Comunidade"),
            ft.Container(
                content=ft.Column(
                    itens,
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                    auto_scroll=True,
                    expand=True,
                ),
                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                expand=True,
                bgcolor=t.FUNDO_CLARO,
            ),
            ft.Container(
                content=ft.Row(
                    [
                        campo_texto,
                        ft.Container(
                            content=ft.Icon(t.ICONES["enviar"], color=t.BRANCO, size=20),
                            width=46,
                            height=46,
                            bgcolor=t.VERDE_PRIMARIO,
                            border_radius=23,
                            alignment=ft.Alignment.CENTER,
                            on_click=enviar,
                            tooltip="Enviar",
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                bgcolor=t.BRANCO,
                border=ft.Border.only(top=ft.BorderSide(1, t.BORDA)),
            ),
        ],
        spacing=0,
        expand=True,
    )
