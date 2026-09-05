"""Aba Publicar — o botão central "+" da navegação inferior."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from mobile import theme as t

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App


def _opcao(
    titulo: str, descricao: str, icone: ft.IconData, cor: str, on_click
) -> ft.Container:
    """Cartão grande de escolha entre pedir e oferecer."""
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(icone, size=26, color=t.BRANCO),
                    width=56,
                    height=56,
                    bgcolor=cor,
                    border_radius=16,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column(
                    [
                        ft.Text(
                            titulo, size=16, weight=ft.FontWeight.BOLD, color=t.AZUL_INSTITUCIONAL
                        ),
                        ft.Text(descricao, size=12, color=t.TEXTO_SECUNDARIO),
                    ],
                    spacing=4,
                    expand=True,
                ),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=t.BORDA),
            ],
            spacing=14,
        ),
        padding=18,
        bgcolor=t.BRANCO,
        border_radius=t.RAIO,
        border=ft.Border.all(1, t.BORDA),
        on_click=on_click,
        ink=True,
    )


def construir(app: App) -> ft.Control:
    """Tela de escolha do que publicar."""
    return ft.Container(
        content=ft.Column(
            [
                t.titulo("O que você quer publicar?", 21),
                t.subtitulo("Escolha abaixo. Leva menos de um minuto."),
                ft.Container(height=12),
                _opcao(
                    "Preciso de ajuda",
                    "Publique o que está faltando para você ou sua comunidade.",
                    ft.Icons.PAN_TOOL_ALT_OUTLINED,
                    t.URGENCIA,
                    lambda _: app.navegar("nova_solicitacao"),
                ),
                _opcao(
                    "Quero ajudar / Doar",
                    "Ofereça um item, transporte ou um ponto de retirada.",
                    ft.Icons.VOLUNTEER_ACTIVISM,
                    t.VERDE_PRIMARIO,
                    lambda _: app.navegar("nova_oferta"),
                ),
                ft.Container(height=8),
                t.cartao(
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.CRISIS_ALERT, color=t.URGENCIA),
                            ft.Column(
                                [
                                    ft.Text(
                                        "Modo emergência",
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                        color=t.AZUL_INSTITUCIONAL,
                                    ),
                                    ft.Text(
                                        "Ao publicar um pedido você pode marcá-lo como "
                                        "emergência: ele vai para o topo das listas e ganha "
                                        "destaque no mapa.",
                                        size=11,
                                        color=t.TEXTO_SECUNDARIO,
                                    ),
                                ],
                                spacing=3,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                    ),
                    cor="#FDECEC",
                    borda="#F5C9C9",
                ),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        padding=ft.Padding.symmetric(horizontal=16, vertical=18),
        expand=True,
        bgcolor=t.FUNDO_CLARO,
    )
