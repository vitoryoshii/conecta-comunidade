"""Tela 3 — Login."""

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
    """Formulário de acesso: e-mail, senha e atalhos de demonstração."""
    campo_email = t.campo(
        "E-mail", icone=ft.Icons.MAIL_OUTLINE, tipo_teclado=ft.KeyboardType.EMAIL
    )
    campo_senha = t.campo("Senha", senha=True, icone=ft.Icons.LOCK_OUTLINE)

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

    def usar_conta_demo(email: str) -> None:
        """Preenche o formulário com uma das contas do seed."""
        campo_email.value = email
        campo_senha.value = "senha123"
        app.page.update()

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.IconButton(
                            ft.Icons.ARROW_BACK,
                            icon_color=t.AZUL_INSTITUCIONAL,
                            on_click=app.voltar,
                        )
                    ]
                ),
                ft.Container(height=10),
                ft.Icon(ft.Icons.VOLUNTEER_ACTIVISM, size=44, color=t.VERDE_PRIMARIO),
                t.titulo("Que bom te ver de novo", 24),
                t.subtitulo("Entre para acompanhar seus pedidos e doações."),
                ft.Container(height=18),
                campo_email,
                campo_senha,
                ft.Container(height=6),
                t.botao_primario("Entrar", entrar, ft.Icons.LOGIN, largura=400),
                ft.Row(
                    [
                        t.subtitulo("Ainda não tem conta?"),
                        ft.TextButton(
                            content="Criar agora",
                            on_click=lambda _: app.substituir("cadastro"),
                            style=ft.ButtonStyle(color=t.VERDE_PRIMARIO),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=0,
                ),
                ft.Container(height=10),
                # Bloco de conveniência para a banca: um toque preenche o login.
                t.cartao(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.SCIENCE_OUTLINED,
                                        size=16,
                                        color=t.TEXTO_SECUNDARIO,
                                    ),
                                    t.subtitulo("Contas de demonstração (senha: senha123)"),
                                ],
                                spacing=6,
                            ),
                            ft.Column(
                                [
                                    ft.TextButton(
                                        content=rotulo,
                                        on_click=lambda _, e=email: usar_conta_demo(e),
                                        style=ft.ButtonStyle(color=t.VERDE_ESCURO),
                                    )
                                    for email, rotulo in CONTAS_DEMO
                                ],
                                spacing=0,
                            ),
                        ],
                        spacing=4,
                    ),
                    cor=t.VERDE_SUAVE,
                    borda=t.VERDE_SUAVE,
                ),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        padding=ft.Padding.symmetric(horizontal=24, vertical=12),
        expand=True,
        bgcolor=t.FUNDO_CLARO,
    )
