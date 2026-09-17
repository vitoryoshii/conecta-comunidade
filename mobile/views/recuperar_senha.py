"""Tela 3b — Recuperar senha.

Terceira das telas de autenticação; usa o mesmo andaime visual das outras duas
(`theme.tela_de_autenticacao`).

O `POST /auth/recuperar-senha` responde sempre 200 com a mesma mensagem, exista
ou não uma conta com o e-mail informado — a tela apenas repete essa resposta, de
modo que nada aqui revela quem está cadastrado.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from mobile import theme as t
from mobile.components import campos

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

# Mensagem exibida quando a API não responde: o texto é o mesmo que ela devolve,
# então o usuário vê a tela se comportar igual com ou sem backend no ar.
CONFIRMACAO_PADRAO = "Se o e-mail existir, enviamos um link para redefinir a senha."


def construir(app: App) -> ft.Control:
    """Formulário de um campo só: e-mail para receber o link de redefinição."""
    campo_email = campos.campo_texto(
        "seu@email.com", icone=t.ICONES["email"], tipo_teclado=ft.KeyboardType.EMAIL
    )

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

    return t.tela_de_autenticacao(
        [
            campos.com_rotulo("E-mail", campo_email, sobre_foto=True),
            ft.Container(height=6),
            t.botao_primario(
                "Enviar link",
                enviar,
                largura=t.LARGURA_FORMULARIO,
                cor=t.BRANCO,
                cor_texto=t.VERDE_ESCURO,
            ),
            t.link_claro("Lembrou a senha? Entrar", lambda _: app.voltar()),
        ],
        on_voltar=app.voltar,
        cabecalho=(
            "Recuperar senha",
            "Informe seu e-mail e enviaremos um link para redefinir a senha",
        ),
    )
