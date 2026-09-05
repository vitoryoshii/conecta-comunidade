"""Tela 1 — Splash / Onboarding."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from mobile import theme as t

if TYPE_CHECKING:  # pragma: no cover - apenas para tipagem
    from mobile.main import App


def _logo() -> ft.Container:
    """Marca do produto: mãos em círculo sobre o verde institucional."""
    return ft.Container(
        content=ft.Icon(ft.Icons.VOLUNTEER_ACTIVISM, size=56, color=t.BRANCO),
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

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(expand=True),
                _logo(),
                ft.Container(height=22),
                ft.Text(
                    "Conecta Comunidade",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=t.AZUL_INSTITUCIONAL,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Conectando pessoas, transformando vidas",
                    size=14,
                    color=t.TEXTO_SECUNDARIO,
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
                    "Entrar", lambda _: app.navegar("login"), ft.Icons.LOGIN, largura=320
                ),
                ft.TextButton(
                    content="Continuar como visitante",
                    on_click=continuar_como_visitante,
                    style=ft.ButtonStyle(color=t.TEXTO_SECUNDARIO),
                ),
                ft.Container(height=10),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            expand=True,
        ),
        padding=ft.Padding.symmetric(horizontal=28, vertical=20),
        expand=True,
        bgcolor=t.FUNDO_CLARO,
    )


def _pilar(icone: ft.IconData, rotulo: str) -> ft.Column:
    """Ícone + legenda usados na linha de destaques da abertura."""
    return ft.Column(
        [
            ft.Container(
                content=ft.Icon(icone, size=22, color=t.VERDE_ESCURO),
                width=52,
                height=52,
                bgcolor=t.VERDE_SUAVE,
                border_radius=26,
                alignment=ft.Alignment.CENTER,
            ),
            ft.Text(rotulo, size=11, color=t.TEXTO_SECUNDARIO),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=8,
    )
