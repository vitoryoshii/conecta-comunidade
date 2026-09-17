"""
Botão de ação flutuante (FAB) — publicar.

Publicar é a ação central do app, e ação não é destino: por isso ela saiu da
barra de navegação e virou um botão que flutua sobre o conteúdo, no canto
inferior direito. O gradiente e a sombra colorida o destacam de qualquer tela
sem precisar de moldura.

As telas que rolam reservam `ESPACO_PARA_O_FAB` no fim da lista, para o último
cartão não terminar embaixo do botão.
"""

from typing import Callable

import flet as ft

from mobile import theme as t

LADO = 58
RAIO = 20
LADO_DO_ICONE = 30

# Distância do FAB até as bordas da área de conteúdo.
MARGEM = 20

# Folga no fim das listas roláveis das telas que exibem o FAB.
ESPACO_PARA_O_FAB = 96


def botao_flutuante(
    ao_clicar: Callable[[ft.ControlEvent], None], tooltip: str = "Publicar"
) -> ft.Container:
    """Quadrado arredondado com gradiente teal → verde profundo."""
    return ft.Container(
        content=ft.Icon(t.ICONES["adicionar"], size=LADO_DO_ICONE, color=t.BRANCO),
        width=LADO,
        height=LADO,
        border_radius=RAIO,
        alignment=ft.Alignment.CENTER,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[t.TEAL, t.VERDE_PROFUNDO],
        ),
        shadow=t.SOMBRA_FLUTUANTE,
        on_click=ao_clicar,
        ink=True,
        tooltip=tooltip,
        # Posição dentro do `Stack` da área de conteúdo, em `main.py`.
        right=MARGEM,
        bottom=MARGEM,
    )
