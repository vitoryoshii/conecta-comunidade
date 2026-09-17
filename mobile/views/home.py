"""Tela 4 — Home.

Primeira tela de quem entra. A hierarquia é: quem eu sou (header), onde estou
(localização), o convite do produto (banner), o que posso fazer (duas ações),
por onde procurar (categorias) e o que já está acontecendo perto (lista).

O padrão visual é o premium do app: sombra no lugar de traço, quadrados tom
sobre tom por categoria e chevron nos itens que abrem outra tela.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from mobile import theme as t
from mobile.components.avatar import avatar
from mobile.components.comuns import cartao_solicitacao, secao
from mobile.components.fab import ESPACO_PARA_O_FAB

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

# Fundos suaves dos dois cartões de ação — o par tom sobre tom de cada um.
FUNDO_PEDIR = "#FDEEEE"
FUNDO_DOAR = "#E4F7EE"

# Camadas translúcidas sobre o gradiente do banner: o quadrado "de vidro" do
# ícone e a marca d'água. Em #AARRGGBB, 0x1F ≈ 12% e 0x1A ≈ 10%.
VIDRO = "#1FFFFFFF"
MARCA_DAGUA = "#1AFFFFFF"

LADO_DA_CATEGORIA = 56


def _sino(app: App, nao_lidas: int) -> ft.Container:
    """Sino de notificações em um quadrado branco flutuante."""
    icone: ft.Control = ft.Icon(
        ft.Icons.NOTIFICATIONS_NONE_ROUNDED, size=22, color=t.TEXTO_FORTE
    )
    if nao_lidas:
        # Ponto âmbar em vez de contador: no header, o número competiria com o
        # nome do usuário; o ponto só diz "tem coisa nova".
        icone = ft.Stack(
            [
                icone,
                ft.Container(
                    width=9,
                    height=9,
                    bgcolor=t.AMARELO_ATENCAO,
                    border_radius=5,
                    right=0,
                    top=0,
                ),
            ],
            width=22,
            height=22,
        )

    return ft.Container(
        content=icone,
        width=42,
        height=42,
        bgcolor=t.BRANCO,
        border_radius=t.RAIO_BOTAO,
        alignment=ft.Alignment.CENTER,
        shadow=t.SOMBRA_CARD,
        on_click=lambda _: app.navegar("conversas"),
        ink=True,
        tooltip="Notificações",
    )


def _cabecalho(app: App, usuario: dict[str, Any], nao_lidas: int) -> ft.Control:
    """Avatar, saudação em duas linhas e sino — sem cartão em volta.

    O header não é um cartão: colocar uma superfície branca aqui empurraria o
    banner para baixo e criaria duas caixas empilhadas logo na abertura.
    """
    return ft.Row(
        [
            avatar(usuario),
            ft.Column(
                [
                    ft.Text("Bom te ver,", size=12, color=t.TEXTO_SECUNDARIO),
                    t.titulo(app.state.nome, 18),
                ],
                spacing=0,
                expand=True,
            ),
            _sino(app, nao_lidas),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=12,
    )


def _localizacao(usuario: dict[str, Any]) -> ft.Row:
    """Linha discreta com a cidade/UF do usuário."""
    cidade = usuario.get("cidade") or "Localização não definida"
    estado = usuario.get("estado")
    return ft.Row(
        [
            ft.Icon(t.ICONES["local"], size=15, color=t.VERDE_PRIMARIO),
            t.meta(f"{cidade}, {estado}" if estado else cidade),
        ],
        spacing=5,
    )


def _banner(app: App) -> ft.Container:
    """Convite para o mapa, em gradiente verde com marca d'água."""
    botao = ft.Container(
        content=ft.Row(
            [
                ft.Text(
                    "Abrir o mapa",
                    size=12.5,
                    weight=ft.FontWeight.W_700,
                    color=t.VERDE_PROFUNDO,
                ),
                ft.Icon(t.ICONES["avancar"], size=16, color=t.VERDE_PROFUNDO),
            ],
            spacing=6,
            tight=True,
        ),
        padding=ft.Padding.symmetric(horizontal=14, vertical=9),
        bgcolor=t.BRANCO,
        border_radius=t.RAIO_BOTAO,
        shadow=t.SOMBRA_CARD,
        on_click=lambda _: app.navegar("mapa"),
        ink=True,
    )

    return ft.Container(
        content=ft.Stack(
            [
                # Marca d'água: grande, cortada pelo canto e quase transparente.
                ft.Icon(
                    t.ICONES["doacoes"],
                    size=150,
                    color=MARCA_DAGUA,
                    right=-28,
                    bottom=-34,
                ),
                ft.Container(
                    content=ft.Icon(t.ICONES["estado"], size=20, color=t.BRANCO),
                    width=38,
                    height=38,
                    bgcolor=VIDRO,
                    border_radius=12,
                    alignment=ft.Alignment.CENTER,
                    right=16,
                    top=16,
                ),
                ft.Column(
                    [
                        ft.Text(
                            "Sua ajuda chega mais rápido perto de você",
                            size=15.5,
                            weight=ft.FontWeight.BOLD,
                            color=t.BRANCO,
                            style=ft.TextStyle(letter_spacing=-0.3),
                        ),
                        ft.Text(
                            "Veja quem precisa a poucos quilômetros daqui.",
                            size=12,
                            color=t.MENTA_CLARA,
                        ),
                        ft.Container(height=4),
                        botao,
                    ],
                    spacing=5,
                    left=18,
                    top=18,
                    right=64,
                ),
            ],
            height=168,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        ),
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[t.VERDE_BANNER, t.VERDE_PROFUNDO],
        ),
        border_radius=22,
        shadow=t.SOMBRA_FLUTUANTE,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )


def _cartao_acao(
    titulo: str, descricao: str, icone: ft.IconData, cor: str, fundo: str, on_click
) -> ft.Container:
    """Um dos dois cartões grandes de ação da Home."""
    return ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Icon(icone, size=23, color=cor),
                    width=46,
                    height=46,
                    bgcolor=fundo,
                    border_radius=t.RAIO_BOTAO,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Container(height=2),
                t.titulo_cartao(titulo),
                ft.Text(descricao, size=11.5, color=t.TEXTO_SECUNDARIO, max_lines=2),
            ],
            spacing=6,
        ),
        padding=16,
        bgcolor=t.BRANCO,
        border_radius=t.RAIO_CARD,
        shadow=t.SOMBRA_CARD,
        on_click=on_click,
        ink=True,
        expand=True,
        height=152,
    )


def _grade_categorias(app: App) -> ft.Control:
    """Grade de categorias; tocar filtra a tela Explorar por aquela categoria."""
    categorias = app.categorias()
    if not categorias:
        return t.subtitulo("Não foi possível carregar as categorias.")

    quadrados: list[ft.Control] = []
    for categoria in categorias:
        cor_icone, cor_fundo = t.cores_da_categoria(categoria.get("icone"))
        quadrados.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            content=t.icone_por_nome(
                                categoria.get("icone", "category"), 24, cor_icone
                            ),
                            width=LADO_DA_CATEGORIA,
                            height=LADO_DA_CATEGORIA,
                            bgcolor=cor_fundo,
                            border_radius=t.RAIO_CATEGORIA,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Text(
                            categoria["nome"],
                            size=10.5,
                            weight=ft.FontWeight.W_500,
                            color=t.TEXTO_FORTE,
                            text_align=ft.TextAlign.CENTER,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            width=LADO_DA_CATEGORIA + 12,
                        ),
                    ],
                    spacing=7,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                on_click=lambda _, c=categoria: app.navegar("explorar", categoria_id=c["id"]),
                padding=ft.Padding.symmetric(vertical=4),
                border_radius=t.RAIO_CATEGORIA,
                ink=True,
            )
        )

    # Rolagem horizontal: são oito categorias, e em 430px não cabem todas.
    return ft.Row(quadrados, spacing=10, scroll=ft.ScrollMode.AUTO, wrap=False)


def _ver_todas(app: App, **parametros: Any) -> ft.Container:
    """Link "Ver todas" com chevron, usado nos títulos de seção."""
    return ft.Container(
        content=ft.Row(
            [
                ft.Text(
                    "Ver todas", size=12, weight=ft.FontWeight.W_600, color=t.VERDE_PRIMARIO
                ),
                ft.Icon(t.ICONES["detalhe"], size=16, color=t.VERDE_PRIMARIO),
            ],
            spacing=2,
            tight=True,
        ),
        on_click=lambda _: app.navegar("explorar", **parametros),
        padding=ft.Padding.symmetric(horizontal=4, vertical=4),
        border_radius=10,
        ink=True,
    )


def construir(app: App) -> ft.Control:
    """Monta a tela inicial: header, banner, ações, categorias e proximidade."""
    usuario: dict[str, Any] = app.state.usuario or {}

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
            spacing=12,
        )
    else:
        lista_proximas = t.area_vazia(
            "Nenhuma solicitação ativa por perto no momento.", ft.Icons.EXPLORE_OFF_OUTLINED
        )

    return ft.Container(
        content=ft.Column(
            [
                _cabecalho(app, usuario, app.nao_lidas()),
                _localizacao(usuario),
                _banner(app),
                ft.Row(
                    [
                        _cartao_acao(
                            "Preciso de ajuda",
                            "Publique o que está faltando",
                            t.ICONES["preciso_de_ajuda"],
                            t.URGENCIA,
                            FUNDO_PEDIR,
                            lambda _: app.navegar("nova_solicitacao"),
                        ),
                        _cartao_acao(
                            "Quero ajudar",
                            "Ofereça itens ou entrega",
                            t.ICONES["doacoes"],
                            t.VERDE_PRIMARIO,
                            FUNDO_DOAR,
                            lambda _: app.navegar("nova_oferta"),
                        ),
                    ],
                    spacing=12,
                ),
                secao("Categorias", _ver_todas(app)),
                _grade_categorias(app),
                secao("Próximas de você", _ver_todas(app)),
                lista_proximas,
                # Folga para o último cartão não terminar embaixo do FAB.
                ft.Container(height=ESPACO_PARA_O_FAB),
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=16),
        expand=True,
        bgcolor=t.FUNDO_CLARO,
    )
