"""Tela 3 — Login.

Uma das três telas de autenticação; todas compartilham o andaime visual
`theme.tela_de_autenticacao` (foto de fundo, disco do logo, campos brancos).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from mobile import theme as t
from mobile.components import campos

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
    enviando = False
    status = t.status_de_processamento()

    def atualizar_envio(ativo: bool) -> None:
        """Espelha o estado real da operação no botão e na região acessível."""
        nonlocal enviando
        enviando = ativo
        botao_entrar.disabled = ativo
        botao_entrar.content = (
            t.conteudo_de_botao_carregando(
                "Entrando…", t.VERDE_ESCURO, app.reduzir_movimento
            )
            if ativo
            else "Entrar"
        )
        status.label = "Entrando. Aguarde." if ativo else "Pronto para entrar"
        status.value = "ocupado" if ativo else "disponível"
        status.content = ft.Container(width=0, height=0)
        app.page.update()

    async def entrar(_: ft.ControlEvent) -> None:
        """Valida e autentica sem bloquear a atualização da interface."""
        if enviando:
            return
        email = campo_email.value.strip()
        senha = campo_senha.value

        if not email or not senha:
            app.aviso("Preencha e-mail e senha.", erro=True)
            return

        atualizar_envio(True)
        try:
            resposta = await app.executar_assincrono(lambda: app.api.login(email, senha))
            if resposta is None:
                return
            if await app.concluir_autenticacao(resposta["access_token"]):
                app.aviso(f"Bem-vindo(a), {app.state.nome}!")
        finally:
            # Em sucesso a tela foi substituída; em falha devolvemos a mesma
            # instância, com os valores digitados intactos, para nova tentativa.
            if app.state.rota_atual.nome == "login":
                atualizar_envio(False)

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

    campo_email = campos.campo_texto(
        "seu@email.com",
        icone=t.ICONES["email"],
        tipo_teclado=ft.KeyboardType.EMAIL,
        ao_enviar=entrar,
    )
    campo_senha = campos.campo_texto(
        "Sua senha", senha=True, icone=t.ICONES["senha"], ao_enviar=entrar
    )
    botao_entrar = t.botao_primario(
        "Entrar",
        entrar,
        largura=t.LARGURA_FORMULARIO,
        cor=t.BRANCO,
        cor_texto=t.VERDE_ESCURO,
    )

    return t.tela_de_autenticacao(
        [
            campos.com_rotulo("E-mail", campo_email, sobre_foto=True),
            campos.com_rotulo("Senha", campo_senha, sobre_foto=True),
            # Alinhado à direita, logo abaixo do campo de senha.
            ft.Row(
                [t.link_claro("Esqueceu a senha?", lambda _: app.navegar("recuperar_senha"))],
                alignment=ft.MainAxisAlignment.END,
            ),
            ft.Container(height=2),
            botao_entrar,
            status,
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
                        ft.Icon(t.ICONES["demonstracao"], size=13, color=t.MENTA_CLARA),
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
