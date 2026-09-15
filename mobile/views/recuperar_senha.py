"""Tela 3b — Recuperar senha.

Mesma linguagem visual do login: a foto de fundo da marca, o disco branco com o
símbolo e campos brancos sobre o overlay que já vem na imagem.

O `POST /auth/recuperar-senha` responde sempre 200 com a mesma mensagem, exista
ou não uma conta com o e-mail informado — a tela apenas repete essa resposta, de
modo que nada aqui revela quem está cadastrado.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from mobile import theme as t
from mobile.views.login import LOGIN_BG

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

# Mensagem exibida quando a API não responde: o texto é o mesmo que ela devolve,
# então o usuário vê a tela se comportar igual com ou sem backend no ar.
CONFIRMACAO_PADRAO = "Se o e-mail existir, enviamos um link para redefinir a senha."


def construir(app: App) -> ft.Control:
    """Formulário de um campo só: e-mail para receber o link de redefinição."""
    campo_email = t.campo_claro("seu@email.com", tipo_teclado=ft.KeyboardType.EMAIL)

    def enviar(_: ft.ControlEvent) -> None:
        """Pede o link à API e confirma sem revelar se o e-mail existe."""
        email = campo_email.value.strip()
        if not email:
            app.aviso("Informe o e-mail da sua conta.", erro=True)
            return

        resposta = app.executar(lambda: app.api.recuperar_senha(email))
        if resposta is None:
            return

        app.aviso(resposta.get("mensagem") or CONFIRMACAO_PADRAO)
        app.voltar()

    formulario = t.formulario_centralizado(
        [
            t.logo_circular(60),
            ft.Container(height=14),
            ft.Text(
                "Recuperar senha",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=t.BRANCO,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                "Informe seu e-mail e enviaremos um link para redefinir a senha",
                size=12,
                color=t.MENTA_CLARA,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(height=20),
            ft.Column(
                [t.rotulo_claro("E-mail"), campo_email],
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
            ft.Container(height=6),
            t.botao_primario(
                "Enviar link",
                enviar,
                largura=t.LARGURA_FORMULARIO,
                cor=t.BRANCO,
                cor_texto=t.VERDE_ESCURO,
            ),
            t.link_claro("Lembrou a senha? Entrar", lambda _: app.voltar()),
        ]
    )

    conteudo = ft.Container(
        content=ft.Stack(
            [
                formulario,
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
