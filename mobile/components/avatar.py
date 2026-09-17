"""
Avatar do usuário — foto quando existe, inicial estilizada quando não existe.

Fica em um arquivo só porque o fallback é a parte que mais se repete: sem ele,
cada tela inventaria um jeito diferente de desenhar a inicial, e um cadastro sem
foto (a maioria, no começo) pareceria um erro de carregamento em vez de um
estado normal.

A foto vem de `usuario["avatar_url"]`, que hoje guarda um caminho local escolhido
no Perfil. Se o arquivo sumir ou não puder ser lido, o `error_content` do
`ft.Image` devolve a inicial — a tela nunca fica com um buraco.
"""

from typing import Any

import flet as ft

from mobile import theme as t

LADO_PADRAO = 46


def _inicial(nome: str, lado: int) -> ft.Container:
    """Disco com a primeira letra do nome, em gradiente da marca."""
    letra = (nome or "?").strip()[:1].upper() or "?"
    return ft.Container(
        content=ft.Text(
            letra,
            size=lado * 0.42,
            weight=ft.FontWeight.BOLD,
            color=t.BRANCO,
        ),
        width=lado,
        height=lado,
        border_radius=lado / 2,
        alignment=ft.Alignment.CENTER,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[t.VERDE_PRIMARIO, t.VERDE_PROFUNDO],
        ),
    )


def avatar(
    usuario: dict[str, Any] | None,
    lado: int = LADO_PADRAO,
    com_sombra: bool = True,
) -> ft.Container:
    """Avatar circular do usuário, com sombra suave por padrão."""
    usuario = usuario or {}
    nome = str(usuario.get("nome") or "Visitante")
    foto = usuario.get("avatar_url")

    if foto:
        conteudo: ft.Control = ft.Image(
            src=str(foto),
            width=lado,
            height=lado,
            fit=ft.BoxFit.COVER,
            # Recorte no próprio Image: sem isso a foto quadrada vaza pelos
            # cantos do container redondo.
            border_radius=ft.BorderRadius.all(lado / 2),
            error_content=_inicial(nome, lado),
        )
    else:
        conteudo = _inicial(nome, lado)

    return ft.Container(
        content=conteudo,
        width=lado,
        height=lado,
        border_radius=lado / 2,
        shadow=t.SOMBRA_CARD if com_sombra else None,
    )
