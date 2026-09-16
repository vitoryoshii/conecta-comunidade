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
LARGURA_DO_PILAR = 100

# Disco branco de cada pilar e o ícone colorido dentro dele.
LADO_DO_DISCO_DO_PILAR = 64
LADO_DO_ICONE_DO_PILAR = 28


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
                        _pilar(t.ICONES["doacoes"], "Doações"),
                        _pilar(t.ICONES["voluntariado"], "Voluntariado"),
                        _pilar(t.ICONES["emergencias"], "Emergências", cor=t.URGENCIA),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=12,
                ),
                ft.Container(expand=FLEX_ANTES_DOS_BOTOES),
                t.botao_primario(
                    "Criar conta",
                    lambda _: app.navegar("cadastro"),
                    t.ICONES["criar_conta"],
                    largura=320,
                ),
                t.botao_secundario(
                    "Entrar",
                    lambda _: app.navegar("login"),
                    t.ICONES["entrar"],
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


def _pilar(icone: ft.IconData, rotulo: str, cor: str = t.VERDE_PRIMARIO) -> ft.Column:
    """Ícone + legenda usados na linha de destaques da abertura.

    O disco é branco sólido, e não um verde translúcido: sobre a foto, o
    translúcido deixava a borda indefinida e "sujava" a imagem por baixo. Com o
    branco opaco mais uma sombra curta, o ícone descola do fundo e a cor dele
    passa a carregar o significado (verde para ajuda, vermelho para urgência).
    """
    return ft.Column(
        [
            ft.Container(
                content=ft.Icon(icone, size=LADO_DO_ICONE_DO_PILAR, color=cor),
                width=LADO_DO_DISCO_DO_PILAR,
                height=LADO_DO_DISCO_DO_PILAR,
                bgcolor=t.BRANCO,
                border_radius=LADO_DO_DISCO_DO_PILAR / 2,
                alignment=ft.Alignment.CENTER,
                shadow=ft.BoxShadow(blur_radius=8, color="#330E2A47", offset=ft.Offset(0, 3)),
            ),
            ft.Text(
                rotulo,
                size=14,
                weight=ft.FontWeight.W_500,
                color=t.BRANCO,
                text_align=ft.TextAlign.CENTER,
                # A foto tem trechos claros; a sombra segura o texto neles.
                # No Flet 0.86 a sombra de texto vem pelo TextStyle, não pelo Text.
                style=ft.TextStyle(
                    shadow=ft.BoxShadow(blur_radius=4, color="#660E2A47", offset=ft.Offset(0, 1))
                ),
            ),
        ],
        width=LARGURA_DO_PILAR,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10,
    )
