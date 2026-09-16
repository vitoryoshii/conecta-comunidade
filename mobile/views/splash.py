"""Tela 1 — Splash / Onboarding."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from mobile import theme as t

if TYPE_CHECKING:  # pragma: no cover - apenas para tipagem
    from mobile.main import App

# Os dois espaçadores flexíveis dividem a sobra vertical nesta proporção: o de
# baixo fica com a fatia maior, o que empurra o miolo para cima e deixa a
# margem superior generosa sem depender da altura exata do aparelho.
FLEX_ACIMA_DO_LOGO = 2
FLEX_ANTES_DOS_BOTOES = 3

# Largura fixa de cada pilar: sem ela, as legendas ("Doações" e "Voluntariado"
# têm larguras bem diferentes) deixariam os círculos desalinhados entre si.
LARGURA_DO_PILAR = 92


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
                ft.Container(expand=FLEX_ACIMA_DO_LOGO),
                t.logo_circular(),
                ft.Container(height=10),
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
                    spacing=12,
                ),
                ft.Container(expand=FLEX_ANTES_DOS_BOTOES),
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
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            expand=True,
        ),
        # Base folgada: sem ela os botões encostam na borda da tela.
        padding=ft.Padding.only(left=28, right=28, top=20, bottom=32),
        expand=True,
    )

    # Mesma foto e mesmo empilhamento das telas de autenticação: a abertura e o
    # login precisam parecer a mesma tela do mesmo produto.
    return t.fundo_foto(conteudo, t.FOTO_DE_FUNDO)


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
            ft.Text(
                rotulo,
                size=11,
                color="#E7F4EC",
                text_align=ft.TextAlign.CENTER,
            ),
        ],
        width=LARGURA_DO_PILAR,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=8,
    )
