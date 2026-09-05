"""Tela 12 — Minhas solicitações (abas por status)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from mobile import theme as t
from mobile.components.comuns import cabecalho, cartao_solicitacao

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

ABAS = [
    ("ativa", "Ativas"),
    ("em_andamento", "Em andamento"),
    ("concluida", "Concluídas"),
]

# Próximo status sugerido para cada estado atual do pedido.
PROXIMO_STATUS = {
    "ativa": ("em_andamento", "Marcar em andamento", ft.Icons.PLAY_ARROW),
    "em_andamento": ("concluida", "Marcar como concluída", ft.Icons.CHECK_CIRCLE_OUTLINE),
}


def construir(app: App) -> ft.Control:
    """Lista os pedidos do usuário logado, separados por status."""
    aba: str = app.state.rota_atual.parametros.get("aba", "ativa")

    solicitacoes: list[dict[str, Any]] = app.executar(
        lambda: app.api.listar_solicitacoes(
            usuario_id=app.state.usuario_id,
            status=aba,
            ordenar_por="recentes",
            **app.coordenadas(),
        )
    ) or []

    def mudar_status(solicitacao: dict[str, Any]) -> None:
        """Avança o pedido para o próximo estado do ciclo de vida."""
        proximo = PROXIMO_STATUS.get(solicitacao["status"])
        if proximo is None:
            return
        if app.executar(
            lambda: app.api.atualizar_solicitacao(solicitacao["id"], {"status": proximo[0]}),
            "Status atualizado.",
        ):
            app.renderizar()

    if solicitacoes:
        cartoes: list[ft.Control] = []
        for solicitacao in solicitacoes:
            acao = PROXIMO_STATUS.get(solicitacao["status"])
            cartoes.append(
                ft.Column(
                    [
                        cartao_solicitacao(
                            solicitacao, lambda i: app.navegar("detalhe_solicitacao", id=i)
                        ),
                        (
                            ft.Row(
                                [
                                    ft.TextButton(
                                        content=acao[1],
                                        icon=acao[2],
                                        on_click=lambda _, s=solicitacao: mudar_status(s),
                                        style=ft.ButtonStyle(color=t.VERDE_ESCURO),
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.END,
                            )
                            if acao
                            else ft.Container(height=0)
                        ),
                    ],
                    spacing=0,
                )
            )
        lista: ft.Control = ft.Column(cartoes, spacing=8)
    else:
        lista = t.area_vazia(
            "Nenhuma solicitação nesta aba.", ft.Icons.ASSIGNMENT_OUTLINED
        )

    return ft.Column(
        [
            cabecalho("Minhas solicitações", app.voltar),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Text(
                                        rotulo,
                                        size=12,
                                        weight=ft.FontWeight.W_600,
                                        color=t.BRANCO if chave == aba else t.TEXTO_SECUNDARIO,
                                    ),
                                    padding=ft.Padding.symmetric(horizontal=14, vertical=9),
                                    bgcolor=t.VERDE_PRIMARIO if chave == aba else t.BRANCO,
                                    border_radius=20,
                                    border=ft.Border.all(
                                        1, t.VERDE_PRIMARIO if chave == aba else t.BORDA
                                    ),
                                    on_click=lambda _, c=chave: app.substituir(
                                        "minhas_solicitacoes", aba=c
                                    ),
                                )
                                for chave, rotulo in ABAS
                            ],
                            spacing=8,
                        ),
                        t.botao_primario(
                            "Nova solicitação",
                            lambda _: app.navegar("nova_solicitacao"),
                            ft.Icons.ADD,
                            400,
                        ),
                        ft.Container(height=2),
                        lista,
                        ft.Container(height=10),
                    ],
                    spacing=12,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
                padding=ft.Padding.symmetric(horizontal=16, vertical=14),
                expand=True,
                bgcolor=t.FUNDO_CLARO,
            ),
        ],
        spacing=0,
        expand=True,
    )
