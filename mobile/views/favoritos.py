"""Tela de Favoritos — os pedidos que o usuário guardou para depois.

Usa o mesmo cartão da Home e do Explorar, porque é o mesmo conteúdo: mudar o
desenho aqui faria o pedido parecer outra coisa só por estar guardado. A API já
devolve as solicitações inteiras, então a lista não precisa de uma requisição
por item.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from mobile import theme as t
from mobile.components.comuns import cabecalho, cartao_solicitacao
from mobile.components.fab import ESPACO_PARA_O_FAB

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

VAZIO = (
    "Você ainda não favoritou nada.\n"
    "Toque no coração de uma solicitação para guardá-la aqui."
)


def construir(app: App) -> ft.Control:
    """Lista as solicitações favoritadas."""
    favoritos: list[dict[str, Any]] = app.executar(lambda: app.api.listar_favoritos()) or []

    if favoritos:
        lista: ft.Control = ft.Column(
            [
                cartao_solicitacao(
                    item,
                    lambda i: app.navegar("detalhe_solicitacao", id=i),
                    # Tudo nesta tela está guardado: o coração só solta.
                    ao_favoritar=lambda i: app.alternar_favorito(i, True),
                )
                for item in favoritos
            ],
            spacing=12,
        )
    else:
        lista = t.area_vazia(VAZIO, ft.Icons.FAVORITE_BORDER_ROUNDED)

    corpo = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        t.subtitulo(
                            f"{len(favoritos)} pedido{'s' if len(favoritos) != 1 else ''} "
                            "guardado" + ("s" if len(favoritos) != 1 else "")
                        ),
                    ]
                ),
                lista,
                ft.Container(height=ESPACO_PARA_O_FAB),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=16),
        expand=True,
        bgcolor=t.FUNDO_CLARO,
    )

    return ft.Column(
        [cabecalho("Favoritos", ao_voltar=app.voltar), corpo],
        spacing=0,
        expand=True,
    )
