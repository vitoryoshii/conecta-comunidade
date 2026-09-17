"""Tela de troca de senha.

Três campos: a senha atual, a nova e a confirmação — com o mesmo retorno ao vivo
do cadastro (vermelho ao divergir, verde ao coincidir). A senha atual é exigida
pela API, e não só pela tela: estar logado não basta para trocar a senha.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from mobile import theme as t
from mobile.components import campos
from mobile.api_client import ErroApi
from mobile.components.comuns import cabecalho

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

MINIMO_DE_SENHA = 6

SENHAS_IGUAIS = "As senhas coincidem"
SENHAS_DIFERENTES = "As senhas não coincidem"


def construir(app: App) -> ft.Control:
    """Formulário de troca de senha."""
    status = ft.Container(visible=False)

    def conferir(_: ft.ControlEvent | None = None) -> None:
        """Feedback ao vivo da confirmação, a cada tecla."""
        nova = campo_nova.value or ""
        confirmacao = campo_confirmacao.value or ""

        if not confirmacao:
            status.visible = False
        else:
            coincidem = confirmacao == nova and len(nova) >= MINIMO_DE_SENHA
            status.visible = True
            status.content = t.status_claro(
                SENHAS_IGUAIS if coincidem else SENHAS_DIFERENTES, ok=coincidem
            )
            if coincidem:
                campo_confirmacao.error = None

        botao.disabled = not (
            campo_atual.value
            and len(nova) >= MINIMO_DE_SENHA
            and confirmacao == nova
        )
        app.page.update()

    campo_atual = campos.campo_texto(
        "Sua senha de hoje", senha=True, icone=t.ICONES["senha"], ao_mudar=conferir
    )
    campo_nova = campos.campo_texto(
        "Mínimo 6 caracteres",
        senha=True,
        icone=t.ICONES["confirmar_senha"],
        ao_mudar=conferir,
    )
    campo_confirmacao = campos.campo_texto(
        "Repita a senha nova",
        senha=True,
        icone=t.ICONES["confirmar_senha"],
        ao_mudar=conferir,
    )

    def trocar(_: ft.ControlEvent) -> None:
        """Valida na tela e envia; a API confere a senha atual."""
        atual = campo_atual.value or ""
        nova = campo_nova.value or ""
        confirmacao = campo_confirmacao.value or ""

        campo_atual.error = None if atual else "Informe sua senha atual."
        campo_nova.error = (
            None if len(nova) >= MINIMO_DE_SENHA else "Mínimo de 6 caracteres."
        )
        campo_confirmacao.error = None if confirmacao == nova else SENHAS_DIFERENTES
        app.page.update()
        if campo_atual.error or campo_nova.error or campo_confirmacao.error:
            return

        if nova == atual:
            campo_nova.error = "A nova senha precisa ser diferente da atual."
            app.page.update()
            return

        # Aqui não dá para usar `app.executar`: a rota responde 204, então um
        # retorno vazio não distingue sucesso de falha. O erro é tratado na mão.
        try:
            app.api.trocar_senha(atual, nova)
        except ErroApi as erro:
            if erro.status == 400:
                # A recusa é quase sempre a senha atual: marcar o campo é mais
                # útil do que só um aviso que some em três segundos.
                campo_atual.error = erro.mensagem
                app.page.update()
            else:
                app.aviso(erro.mensagem, erro=True)
            return

        app.aviso("Senha alterada com sucesso.")
        app.voltar()

    botao = t.botao_primario("Alterar senha", trocar, t.ICONES["senha"], 400)
    botao.disabled = True

    corpo = ft.Container(
        content=ft.Column(
            [
                t.cartao(
                    ft.Row(
                        [
                            ft.Icon(t.ICONES["privacidade"], size=20, color=t.VERDE_PRIMARIO),
                            ft.Text(
                                "Pedimos sua senha atual porque estar logado não deve "
                                "bastar para trocar a senha da conta.",
                                size=11.5,
                                color=t.TEXTO_SECUNDARIO,
                                expand=True,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=12,
                ),
                ft.Container(height=2),
                campos.com_rotulo("Senha atual", campo_atual),
                campos.com_rotulo("Nova senha", campo_nova),
                campos.com_rotulo("Confirmar nova senha", campo_confirmacao),
                status,
                ft.Container(height=8),
                botao,
                ft.Container(height=20),
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
        [cabecalho("Alterar senha", ao_voltar=app.voltar), corpo],
        spacing=0,
        expand=True,
    )
