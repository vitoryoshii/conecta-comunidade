"""Tela 3 — Login.

Uma das três telas de autenticação; todas compartilham o andaime visual
`theme.tela_de_autenticacao` (foto de fundo, disco do logo, campos brancos).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from mobile import theme as t

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

# Contas criadas pelo `seed.py`, mostradas como atalho na apresentação.
CONTAS_DEMO = [
    ("ana@conecta.com", "Ana · solicitante"),
    ("carlos@conecta.com", "Carlos · doador"),
    ("juliana@conecta.com", "Juliana · voluntária"),
]


def construir(app: App) -> ft.Control:
    """Formulário de acesso, com atalhos para as contas de demonstração."""
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

    return t.tela_de_autenticacao(
        [
            t.campo_rotulado("E-mail", campo_email),
            t.campo_rotulado("Senha", campo_senha),
            # Alinhado à direita, logo abaixo do campo de senha.
            ft.Row(
                [t.link_claro("Esqueceu a senha?", lambda _: app.navegar("recuperar_senha"))],
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
        ],
        on_voltar=app.voltar,
        cabecalho=("Que bom te ver de novo", "Entre para acompanhar seus pedidos"),
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
