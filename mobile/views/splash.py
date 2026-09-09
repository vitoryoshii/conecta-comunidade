"""Tela 1 — Splash / Onboarding."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import flet as ft

from mobile import theme as t

if TYPE_CHECKING:  # pragma: no cover - apenas para tipagem
    from mobile.main import App

RAIZ_MOBILE = Path(__file__).resolve().parent.parent
SPLASH_BACKGROUNDS = (
    RAIZ_MOBILE / "assets" / "img" / "splash-bg.jpg",
    RAIZ_MOBILE / "assets" / "brand" / "img" / "splash-bg.svg",
)
LOGO_SYMBOLS = (
    RAIZ_MOBILE / "assets" / "brand" / "logo-symbol.svg",
    RAIZ_MOBILE / "assets" / "brand" / "logo" / "logo-symbol.svg",
)


def _logo() -> ft.Container:
    """Marca do produto: usa o SVG novo quando estiver disponível."""
    conteudo: ft.Control
    logo = next((caminho for caminho in LOGO_SYMBOLS if caminho.exists()), None)
    if logo:
        conteudo = ft.Image(src=str(logo), width=70, height=70, fit=ft.BoxFit.CONTAIN)
    else:
        conteudo = ft.Icon(ft.Icons.VOLUNTEER_ACTIVISM, size=56, color=t.BRANCO)

    return ft.Container(
        content=conteudo,
        width=112,
        height=112,
        border_radius=56,
        alignment=ft.Alignment.CENTER,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[t.VERDE_PRIMARIO, t.VERDE_ESCURO],
        ),
        shadow=ft.BoxShadow(blur_radius=24, color="#402E9E5B", offset=ft.Offset(0, 10)),
    )


def construir(app: App) -> ft.Control:
    """Monta a tela de entrada com as três formas de acesso."""

    def continuar_como_visitante(_: ft.ControlEvent) -> None:
        """Modo somente-leitura: dá para explorar, mas não publicar."""
        app.state.entrar_como_visitante()
        app.aviso("Você está navegando como visitante.")
        app.reiniciar("home")

    conteudo = ft.Container(
        content=ft.Column(
            [
                ft.Container(expand=True),
                _logo(),
                ft.Container(height=22),
                ft.Text(
                    "Conecta Comunidade",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=t.BRANCO,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Conectando pessoas, transformando vidas",
                    size=14,
                    color="#E7F4EC",
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=28),
                # Três pilares do produto, resumidos em uma linha de ícones.
                ft.Row(
                    [
                        _pilar(ft.Icons.FAVORITE_BORDER, "Doações"),
                        _pilar(ft.Icons.GROUPS_OUTLINED, "Voluntariado"),
                        _pilar(ft.Icons.CRISIS_ALERT, "Emergências"),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=26,
                ),
                ft.Container(expand=True),
                t.botao_primario(
                    "Criar conta",
                    lambda _: app.navegar("cadastro"),
                    ft.Icons.PERSON_ADD_ALT,
                    largura=320,
                ),
                t.botao_secundario(
                    "Entrar",
                    lambda _: app.navegar("login"),
                    ft.Icons.LOGIN,
                    largura=320,
                    cor=t.BRANCO,
                ),
                ft.TextButton(
                    content="Continuar como visitante",
                    on_click=continuar_como_visitante,
                    style=ft.ButtonStyle(color="#E7F4EC"),
                ),
                ft.Container(height=10),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            expand=True,
        ),
        padding=ft.Padding.symmetric(horizontal=28, vertical=20),
        expand=True,
        bgcolor="#D91B6B3A",
    )

    fundo: ft.Control
    splash_bg = next((caminho for caminho in SPLASH_BACKGROUNDS if caminho.exists()), None)
    if splash_bg:
        fundo = ft.Image(
            src=str(splash_bg),
            fit=ft.BoxFit.COVER,
            left=0,
            top=0,
            right=0,
            bottom=0,
        )
    else:
        fundo = ft.Container(
            left=0,
            top=0,
            right=0,
            bottom=0,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=[t.VERDE_PRIMARIO, t.VERDE_ESCURO],
            ),
        )

    return ft.Container(
        content=ft.Stack(
            [
                fundo,
                ft.Container(left=0, top=0, right=0, bottom=0, bgcolor="#D91B6B3A"),
                conteudo,
            ],
            expand=True,
        ),
        expand=True,
        bgcolor=t.VERDE_ESCURO,
    )


def _pilar(icone: ft.IconData, rotulo: str) -> ft.Column:
    """Ícone + legenda usados na linha de destaques da abertura."""
    return ft.Column(
        [
            ft.Container(
                content=ft.Icon(icone, size=22, color=t.BRANCO),
                width=52,
                height=52,
                bgcolor="#332E9E5B",
                border_radius=26,
                alignment=ft.Alignment.CENTER,
            ),
            ft.Text(rotulo, size=11, color="#E7F4EC"),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=8,
    )
