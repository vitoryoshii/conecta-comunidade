"""
Barra de navegação inferior.

Cinco destinos de mesmo peso — Início, Explorar, Mapa, Mensagens e Perfil. O
"+" saiu daqui e virou o FAB flutuante (`components/fab.py`): misturar uma ação
(publicar) com destinos (para onde ir) no mesmo lugar obrigava um item a ter
tamanho e cor próprios, e era isso que desalinhava a barra.

Construímos a barra à mão, em vez de usar `ft.NavigationBar`, para controlar
tamanho de ícone, peso do rótulo e a sombra que ela projeta para cima.
"""

from typing import Callable

import flet as ft

from mobile import theme as t

# (rota, ícone inativo, ícone ativo, rótulo). O par sai sempre da MESMA família:
# contornado quando inativo, cheio/rounded quando ativo — é o que dá a leitura
# imediata de qual aba está selecionada sem depender só da cor.
DESTINOS = [
    ("home", ft.Icons.HOME_OUTLINED, ft.Icons.HOME_ROUNDED, "Início"),
    ("explorar", ft.Icons.SEARCH_OUTLINED, ft.Icons.SEARCH_ROUNDED, "Explorar"),
    ("mapa", ft.Icons.MAP_OUTLINED, ft.Icons.MAP_ROUNDED, "Mapa"),
    ("conversas", ft.Icons.CHAT_BUBBLE_OUTLINE, ft.Icons.CHAT_BUBBLE_ROUNDED, "Mensagens"),
    ("perfil", ft.Icons.PERSON_OUTLINE, ft.Icons.PERSON_ROUNDED, "Perfil"),
]

LADO_DO_ICONE = 22
TAMANHO_DO_ROTULO = 9.5


def _badge(icone: ft.Control, quantidade: int) -> ft.Control:
    """Contador de não lidas sobre o ícone de mensagens."""
    return ft.Stack(
        [
            icone,
            ft.Container(
                content=ft.Text(
                    str(quantidade) if quantidade < 10 else "9+",
                    size=9,
                    color=t.BRANCO,
                    weight=ft.FontWeight.BOLD,
                ),
                bgcolor=t.URGENCIA,
                width=16,
                height=16,
                border_radius=8,
                alignment=ft.Alignment.CENTER,
                left=12,
                top=-4,
            ),
        ],
        width=32,
        height=LADO_DO_ICONE,
    )


def barra_de_navegacao(
    rota_ativa: str, ao_selecionar: Callable[[str], None], nao_lidas: int = 0
) -> ft.Container:
    """Barra branca com os cinco destinos do app."""
    itens: list[ft.Control] = []

    for rota, icone, icone_ativo, rotulo in DESTINOS:
        ativo = rota == rota_ativa
        cor = t.VERDE_PRIMARIO if ativo else t.TEXTO_INATIVO

        icone_control: ft.Control = ft.Icon(
            icone_ativo if ativo else icone, size=LADO_DO_ICONE, color=cor
        )
        if rota == "conversas" and nao_lidas > 0:
            icone_control = _badge(icone_control, nao_lidas)

        itens.append(
            ft.Container(
                content=ft.Column(
                    [
                        icone_control,
                        ft.Text(
                            rotulo,
                            size=TAMANHO_DO_ROTULO,
                            color=cor,
                            weight=ft.FontWeight.W_600 if ativo else ft.FontWeight.W_500,
                        ),
                    ],
                    spacing=3,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                on_click=lambda _, r=rota: ao_selecionar(r),
                expand=True,
                padding=ft.Padding.symmetric(vertical=9),
                alignment=ft.Alignment.CENTER,
            )
        )

    return ft.Container(
        content=ft.Row(itens, alignment=ft.MainAxisAlignment.SPACE_EVENLY),
        bgcolor=t.BRANCO,
        padding=ft.Padding.symmetric(horizontal=4, vertical=2),
        # Sombra para cima no lugar do traço: separa a barra do conteúdo sem
        # desenhar uma linha cinza atravessando a tela.
        shadow=t.SOMBRA_NAV,
    )
