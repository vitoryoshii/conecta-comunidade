"""Aba Mensagens — lista de conversas que dá acesso ao chat."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from mobile import theme as t
from mobile.components.comuns import cartao_conversa

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App


def construir(app: App) -> ft.Control:
    """Monta a lista de conversas do usuário logado."""
    conversas = app.executar(lambda: app.api.listar_conversas()) or []

    def abrir(conversa: dict[str, Any]) -> None:
        """Abre o chat com o interlocutor escolhido."""
        app.navegar(
            "chat",
            com=conversa["interlocutor_id"],
            nome=conversa["interlocutor_nome"],
            solicitacao_id=conversa.get("solicitacao_id"),
            solicitacao_titulo=conversa.get("solicitacao_titulo"),
        )

    if conversas:
        lista: ft.Control = ft.Column(
            [cartao_conversa(conversa, abrir) for conversa in conversas], spacing=10
        )
    else:
        lista = t.area_vazia(
            "Nenhuma conversa ainda.\nEnvie uma proposta em algum pedido para começar.",
            ft.Icons.FORUM_OUTLINED,
        )

    total_nao_lidas = sum(conversa.get("nao_lidas", 0) for conversa in conversas)

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        t.titulo("Mensagens", 22),
                        (
                            t.etiqueta(f"{total_nao_lidas} não lida(s)", cor_texto=t.BRANCO,
                                       cor_fundo=t.URGENCIA)
                            if total_nao_lidas
                            else ft.Container(width=0)
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                t.subtitulo("Converse com quem está ajudando ou pedindo ajuda."),
                ft.Container(height=6),
                lista,
                ft.Container(height=10),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=16),
        expand=True,
        bgcolor=t.FUNDO_CLARO,
    )
