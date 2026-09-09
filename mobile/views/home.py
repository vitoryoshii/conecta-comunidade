"""Tela 4 — Home."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import flet as ft

from mobile import theme as t
from mobile.components.comuns import cartao_solicitacao, secao

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

RAIZ_MOBILE = Path(__file__).resolve().parent.parent
LOGO_SYMBOLS = (
    RAIZ_MOBILE / "assets" / "brand" / "logo-symbol.svg",
    RAIZ_MOBILE / "assets" / "brand" / "logo" / "logo-symbol.svg",
)


def _banner(app: App) -> ft.Container:
    """Faixa de boas-vindas com a mensagem-síntese do produto."""
    return ft.Container(
        content=ft.Stack(
            [
                ft.Column(
                    [
                        ft.Text(
                            "Sua ajuda chega mais rápido perto de você",
                            size=15,
                            weight=ft.FontWeight.BOLD,
                            color=t.BRANCO,
                        ),
                        ft.Text(
                            "Veja quem precisa a poucos quilômetros daqui.",
                            size=12,
                            color="#DFF1E6",
                        ),
                        ft.Container(height=6),
                        ft.OutlinedButton(
                            content="Abrir o mapa",
                            icon=ft.Icons.MAP_OUTLINED,
                            on_click=lambda _: app.navegar("mapa"),
                            style=ft.ButtonStyle(
                                color=t.BRANCO,
                                side=ft.BorderSide(1.2, t.BRANCO),
                                shape=ft.RoundedRectangleBorder(radius=12),
                            ),
                        ),
                    ],
                    spacing=4,
                    width=235,
                ),
                ft.Icon(
                    ft.Icons.HANDSHAKE_OUTLINED,
                    size=118,
                    color="#66FFFFFF",
                    right=-10,
                    bottom=-18,
                ),
            ],
            height=150,
        ),
        padding=18,
        border_radius=t.RAIO,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[t.VERDE_PRIMARIO, t.VERDE_ESCURO],
        ),
    )


def _cartao_acao(
    titulo: str, descricao: str, icone: ft.IconData, cor: str, on_click
) -> ft.Container:
    """Um dos dois cartões grandes de ação da Home."""
    return ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Icon(icone, size=24, color=t.BRANCO),
                    width=46,
                    height=46,
                    bgcolor=cor,
                    border_radius=14,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Text(titulo, size=15, weight=ft.FontWeight.BOLD, color=t.AZUL_INSTITUCIONAL),
                ft.Text(descricao, size=11, color=t.TEXTO_SECUNDARIO),
            ],
            spacing=8,
        ),
        padding=16,
        bgcolor=t.BRANCO,
        border_radius=t.RAIO,
        border=ft.Border.all(1, t.BORDA),
        on_click=on_click,
        ink=True,
        expand=True,
        height=150,
    )


def _grade_categorias(app: App) -> ft.Control:
    """Grade de categorias; tocar filtra a tela Explorar por aquela categoria."""
    categorias = app.categorias()
    if not categorias:
        return t.subtitulo("Não foi possível carregar as categorias.")

    return ft.Row(
        [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            content=t.icone_por_nome(
                                categoria.get("icone", "category"),
                                21,
                                t.CORES_CATEGORIAS[indice % len(t.CORES_CATEGORIAS)][0],
                            ),
                            width=52,
                            height=52,
                            bgcolor=t.CORES_CATEGORIAS[indice % len(t.CORES_CATEGORIAS)][1],
                            border_radius=16,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Text(
                            categoria["nome"],
                            size=10,
                            color=t.TEXTO_SECUNDARIO,
                            text_align=ft.TextAlign.CENTER,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            width=68,
                        ),
                    ],
                    spacing=6,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                on_click=lambda _, c=categoria: app.navegar("explorar", categoria_id=c["id"]),
                padding=ft.Padding.symmetric(vertical=4),
            )
            for indice, categoria in enumerate(categorias)
        ],
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
        wrap=False,
    )


def construir(app: App) -> ft.Control:
    """Monta a tela inicial: saudação, banner, ações, categorias e proximidade."""
    # Pedidos mais próximos (ou os mais recentes, no modo visitante).
    proximas = app.executar(
        lambda: app.api.listar_solicitacoes(
            status="ativa", ordenar_por="distancia", limite=5, **app.coordenadas()
        )
    ) or []

    if proximas:
        lista_proximas: ft.Control = ft.Column(
            [cartao_solicitacao(item, lambda i: app.navegar("detalhe_solicitacao", id=i))
             for item in proximas],
            spacing=10,
        )
    else:
        lista_proximas = t.area_vazia(
            "Nenhuma solicitação ativa por perto no momento.", ft.Icons.EXPLORE_OFF
        )

    marca_home: ft.Control
    logo_path = next((caminho for caminho in LOGO_SYMBOLS if caminho.exists()), None)
    if logo_path:
        marca_home = ft.Image(src=str(logo_path), width=34, height=34, fit=ft.BoxFit.CONTAIN)
    else:
        marca_home = ft.Container(
            content=ft.Icon(ft.Icons.VOLUNTEER_ACTIVISM, size=18, color=t.BRANCO),
            width=34,
            height=34,
            bgcolor=t.VERDE_PRIMARIO,
            border_radius=17,
            alignment=ft.Alignment.CENTER,
        )

    saudacao = ft.Row(
        [
            marca_home,
            ft.Column(
                [
                    ft.Text(f"Olá, {app.state.nome}", size=20, weight=ft.FontWeight.BOLD,
                            color=t.AZUL_INSTITUCIONAL),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.PLACE_OUTLINED, size=13, color=t.TEXTO_SECUNDARIO),
                            ft.Text(
                                (app.state.usuario or {}).get("cidade") or "Localização não definida",
                                size=12,
                                color=t.TEXTO_SECUNDARIO,
                            ),
                        ],
                        spacing=4,
                    ),
                ],
                spacing=2,
                expand=True,
            ),
            ft.IconButton(
                ft.Icons.APARTMENT,
                icon_color=t.AZUL_INSTITUCIONAL,
                tooltip="ONGs e instituições",
                on_click=lambda _: app.navegar("ongs"),
            ),
            ft.CircleAvatar(
                content=ft.Text(
                    app.state.nome[0].upper(), color=t.BRANCO, weight=ft.FontWeight.BOLD
                ),
                bgcolor=t.VERDE_PRIMARIO,
                radius=20,
            ),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    return ft.Container(
        content=ft.Column(
            [
                saudacao,
                _banner(app),
                ft.Row(
                    [
                        _cartao_acao(
                            "Preciso de ajuda",
                            "Publique o que está faltando",
                            ft.Icons.PAN_TOOL_ALT_OUTLINED,
                            t.URGENCIA,
                            lambda _: app.navegar("nova_solicitacao"),
                        ),
                        _cartao_acao(
                            "Quero ajudar / Doar",
                            "Ofereça itens, entrega ou retirada",
                            ft.Icons.VOLUNTEER_ACTIVISM,
                            t.VERDE_PRIMARIO,
                            lambda _: app.navegar("nova_oferta"),
                        ),
                    ],
                    spacing=12,
                ),
                secao("Categorias"),
                _grade_categorias(app),
                secao(
                    "Solicitações próximas de você",
                    ft.TextButton(
                        content="Ver todas",
                        on_click=lambda _: app.navegar("explorar"),
                        style=ft.ButtonStyle(color=t.VERDE_PRIMARIO),
                    ),
                ),
                lista_proximas,
                ft.Container(height=10),
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=16),
        expand=True,
        bgcolor=t.FUNDO_CLARO,
    )
