"""Tela 3 — Login (foto de fundo da identidade visual)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from mobile import theme as t

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

# Foto de mãos que já vem com o overlay verde da marca aplicado — por isso a
# tela não empilha nenhuma camada de cor adicional sobre ela.
LOGIN_BG = "brand/img/login-bg.jpg"

# Contas criadas pelo `seed.py`, mostradas como atalho na apresentação.
CONTAS_DEMO = [
    ("ana@conecta.com", "Ana · solicitante"),
    ("carlos@conecta.com", "Carlos · doador"),
    ("juliana@conecta.com", "Juliana · voluntária"),
]


def construir(app: App) -> ft.Control:
    """Formulário de acesso sobre a foto de fundo, com atalhos de demonstração."""
    campo_email = t.campo_claro("seu@email.com", tipo_teclado=ft.KeyboardType.EMAIL)
    campo_senha = t.campo_claro("Sua senha", senha=True)

    def entrar(_: ft.ControlEvent) -> None:
        """Valida os campos, autentica e guarda o token no estado."""
        email = campo_email.value.strip()
        senha = campo_senha.value

        if not email or not senha:
            app.aviso("Preencha e-mail e senha.", erro=True)
            return

        resposta = app.executar(lambda: app.api.login(email, senha))
        if resposta is None:
            return

        app.api.definir_token(resposta["access_token"])
        app.state.entrar(resposta["access_token"], resposta["usuario"])
        app.aviso(f"Bem-vindo(a), {app.state.nome}!")
        app.reiniciar("home")

    def continuar_como_visitante(_: ft.ControlEvent) -> None:
        """Modo somente-leitura: dá para explorar, mas não publicar."""
        app.state.entrar_como_visitante()
        app.aviso("Você está navegando como visitante.")
        app.reiniciar("home")

    def usar_conta_demo(email: str) -> None:
        """Preenche o formulário com uma das contas do seed."""
        campo_email.value = email
        campo_senha.value = "senha123"
        app.page.update()

    formulario = t.formulario_centralizado(
        [
            t.logo_circular(60),
            ft.Container(height=14),
            ft.Text(
                "Que bom te ver de novo",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=t.BRANCO,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                "Entre para acompanhar seus pedidos",
                size=12,
                color=t.MENTA_CLARA,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(height=20),
            _campo_rotulado("E-mail", campo_email),
            _campo_rotulado("Senha", campo_senha),
            # Alinhado à direita, logo abaixo do campo de senha.
            ft.Row(
                [
                    t.link_claro(
                        "Esqueceu a senha?", lambda _: app.navegar("recuperar_senha")
                    )
                ],
                alignment=ft.MainAxisAlignment.END,
            ),
            ft.Container(height=2),
            t.botao_primario(
                "Entrar",
                entrar,
                largura=t.LARGURA_FORMULARIO,
                cor=t.BRANCO,
                cor_texto=t.VERDE_ESCURO,
            ),
            t.botao_secundario(
                "Criar conta",
                lambda _: app.substituir("cadastro"),
                largura=t.LARGURA_FORMULARIO,
                cor=t.BRANCO,
            ),
            ft.Container(height=4),
            ft.TextButton(
                content="Continuar como visitante",
                on_click=continuar_como_visitante,
                style=ft.ButtonStyle(color=t.MENTA_CLARA),
            ),
            _contas_demo(app, usar_conta_demo),
        ]
    )

    conteudo = ft.Container(
        content=ft.Stack(
            [
                formulario,
                # Botão voltar solto no canto: não empurra o formulário do centro.
                ft.Container(
                    content=ft.IconButton(
                        ft.Icons.ARROW_BACK, icon_color=t.BRANCO, on_click=app.voltar
                    ),
                    left=-12,
                    top=0,
                ),
            ],
            expand=True,
        ),
        padding=ft.Padding.symmetric(horizontal=36, vertical=16),
        expand=True,
    )

    return t.fundo_foto(conteudo, LOGIN_BG)


def _campo_rotulado(rotulo: str, campo: ft.TextField) -> ft.Column:
    """Rótulo branco acima do campo branco, como pede a identidade da tela."""
    return ft.Column(
        [t.rotulo_claro(rotulo), campo],
        spacing=6,
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )


def _contas_demo(app: App, ao_escolher) -> ft.Column:
    """Bloco discreto no rodapé: um toque preenche o login para a banca."""
    lista = ft.Column(
        [
            ft.TextButton(
                content=rotulo,
                on_click=lambda _, e=email: ao_escolher(e),
                style=ft.ButtonStyle(color=t.BRANCO),
            )
            for email, rotulo in CONTAS_DEMO
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        visible=False,
    )

    def alternar(_: ft.ControlEvent) -> None:
        """Mostra ou esconde a lista de contas de demonstração."""
        lista.visible = not lista.visible
        app.page.update()

    return ft.Column(
        [
            ft.TextButton(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.SCIENCE_OUTLINED, size=13, color=t.MENTA_CLARA),
                        ft.Text("Contas de demonstração", size=11, color=t.MENTA_CLARA),
                    ],
                    spacing=5,
                    tight=True,
                ),
                on_click=alternar,
            ),
            lista,
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
