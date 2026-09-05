"""Tela 10 — ONGs e Instituições."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from mobile import theme as t
from mobile.components.comuns import cartao_ong

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App


def construir(app: App) -> ft.Control:
    """Monta a busca e a lista de instituições ordenada por proximidade."""
    parametros = app.state.rota_atual.parametros
    busca: str = parametros.get("busca", "")
    somente_verificadas: bool = parametros.get("verificadas", False)

    campo_busca = ft.TextField(
        value=busca,
        hint_text="Buscar instituição...",
        prefix_icon=ft.Icons.SEARCH,
        filled=True,
        fill_color=t.BRANCO,
        border_radius=14,
        border_color=t.BORDA,
        focused_border_color=t.VERDE_PRIMARIO,
        color=t.AZUL_INSTITUCIONAL,
        on_submit=lambda e: app.substituir(
            "ongs", busca=e.control.value, verificadas=somente_verificadas
        ),
    )

    lista = app.executar(
        lambda: app.api.listar_ongs(
            busca=busca or None,
            somente_verificadas=somente_verificadas or None,
            **app.coordenadas(),
        )
    ) or []

    if lista:
        conteudo: ft.Control = ft.Column(
            [cartao_ong(ong, lambda i: app.navegar("perfil_ong", id=i)) for ong in lista],
            spacing=10,
        )
    else:
        conteudo = t.area_vazia("Nenhuma instituição encontrada.", ft.Icons.APARTMENT)

    filtro_verificadas = ft.Container(
        content=ft.Row(
            [
                ft.Icon(
                    ft.Icons.VERIFIED,
                    size=15,
                    color=t.BRANCO if somente_verificadas else t.VERDE_PRIMARIO,
                ),
                ft.Text(
                    "Somente verificadas",
                    size=12,
                    weight=ft.FontWeight.W_600,
                    color=t.BRANCO if somente_verificadas else t.TEXTO_SECUNDARIO,
                ),
            ],
            spacing=6,
            tight=True,
        ),
        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
        bgcolor=t.VERDE_PRIMARIO if somente_verificadas else t.BRANCO,
        border_radius=20,
        border=ft.Border.all(1, t.VERDE_PRIMARIO if somente_verificadas else t.BORDA),
        on_click=lambda _: app.substituir(
            "ongs", busca=busca, verificadas=not somente_verificadas
        ),
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        t.titulo("ONGs e Instituições", 21),
                        ft.IconButton(
                            ft.Icons.MAP_OUTLINED,
                            icon_color=t.AZUL_INSTITUCIONAL,
                            tooltip="Ver no mapa",
                            on_click=lambda _: app.navegar("mapa", tipos=["ong"]),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                t.subtitulo("Parceiros que recebem doações e coordenam voluntários."),
                campo_busca,
                ft.Row([filtro_verificadas, t.subtitulo(f"{len(lista)} instituição(ões)")],
                       spacing=10),
                ft.Container(height=2),
                conteudo,
                ft.Container(height=10),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        padding=ft.Padding.symmetric(horizontal=16, vertical=14),
        expand=True,
        bgcolor=t.FUNDO_CLARO,
    )
