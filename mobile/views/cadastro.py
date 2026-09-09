"""Tela 2 — Cadastro."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from mobile import theme as t

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

# Tipos de usuário aceitos pela API, com um rótulo amigável e um ícone.
TIPOS = [
    ("solicitante", "Preciso de ajuda", ft.Icons.PAN_TOOL_ALT_OUTLINED),
    ("doador", "Quero doar", ft.Icons.CARD_GIFTCARD),
    ("voluntario", "Sou voluntário(a)", ft.Icons.GROUPS_OUTLINED),
    ("ong", "Represento uma ONG", ft.Icons.APARTMENT),
]

# Localizações pré-definidas: evitam pedir GPS e já deixam o cálculo de
# distância funcionando na primeira execução.
LOCALIDADES = [
    ("Vila Madalena - São Paulo/SP", -23.5545, -46.6896),
    ("Pinheiros - São Paulo/SP", -23.5670, -46.7020),
    ("Butantã - São Paulo/SP", -23.5710, -46.7200),
    ("Centro - São Paulo/SP", -23.5460, -46.6360),
    ("Capão Redondo - São Paulo/SP", -23.6600, -46.7700),
    ("Santo Amaro - São Paulo/SP", -23.6520, -46.7080),
    ("Tatuapé - São Paulo/SP", -23.5400, -46.5760),
]


def construir(app: App) -> ft.Control:
    """Formulário de criação de conta."""
    campo_nome = t.campo("Nome completo", icone=ft.Icons.PERSON_OUTLINE)
    campo_email = t.campo(
        "E-mail", icone=ft.Icons.MAIL_OUTLINE, tipo_teclado=ft.KeyboardType.EMAIL
    )
    campo_senha = t.campo("Senha (mínimo 6 caracteres)", senha=True, icone=ft.Icons.LOCK_OUTLINE)

    seletor_tipo = ft.Dropdown(
        label="Como você quer participar?",
        value="solicitante",
        options=[
            ft.DropdownOption(key=chave, text=rotulo, leading_icon=icone)
            for chave, rotulo, icone in TIPOS
        ],
        filled=True,
        fill_color=t.BRANCO,
        border_radius=12,
        border_color=t.BORDA,
        color=t.AZUL_INSTITUCIONAL,
    )

    seletor_local = ft.Dropdown(
        label="Onde você está?",
        value=LOCALIDADES[0][0],
        options=[ft.DropdownOption(key=nome, text=nome) for nome, _, _ in LOCALIDADES],
        filled=True,
        fill_color=t.BRANCO,
        border_radius=12,
        border_color=t.BORDA,
        color=t.AZUL_INSTITUCIONAL,
    )

    def cadastrar(_: ft.ControlEvent) -> None:
        """Valida o formulário e cria a conta na API."""
        nome = campo_nome.value.strip()
        email = campo_email.value.strip()
        senha = campo_senha.value or ""

        if len(nome) < 2:
            app.aviso("Informe seu nome completo.", erro=True)
            return
        if "@" not in email:
            app.aviso("Informe um e-mail válido.", erro=True)
            return
        if len(senha) < 6:
            app.aviso("A senha precisa ter ao menos 6 caracteres.", erro=True)
            return

        # Converte a localidade escolhida em coordenadas.
        cidade = seletor_local.value
        latitude, longitude = next(
            ((lat, lon) for nome_local, lat, lon in LOCALIDADES if nome_local == cidade),
            (LOCALIDADES[0][1], LOCALIDADES[0][2]),
        )

        resposta = app.executar(
            lambda: app.api.registrar(
                {
                    "nome": nome,
                    "email": email,
                    "senha": senha,
                    "tipo": seletor_tipo.value,
                    "cidade": cidade,
                    "latitude": latitude,
                    "longitude": longitude,
                }
            )
        )
        if resposta is None:
            return

        app.api.definir_token(resposta["access_token"])
        app.state.entrar(resposta["access_token"], resposta["usuario"])
        app.aviso("Conta criada! Bem-vindo(a) ao Conecta Comunidade.")
        app.reiniciar("home")

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
                ft.Container(height=6),
                t.titulo("Criar sua conta", 24),
                t.subtitulo("Leva menos de um minuto. Seus dados ficam protegidos."),
                ft.Container(height=14),
                campo_nome,
                campo_email,
                campo_senha,
                seletor_tipo,
                seletor_local,
                ft.Row(
                    [
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=14, color=t.TEXTO_SECUNDARIO),
                        ft.Text(
                            "Usamos sua região apenas para mostrar pedidos próximos.",
                            size=11,
                            color=t.TEXTO_SECUNDARIO,
                            expand=True,
                        ),
                    ],
                    spacing=6,
                ),
                ft.Container(height=6),
                t.botao_primario("Criar conta", cadastrar, ft.Icons.CHECK, largura=400),
                ft.Row(
                    [
                        t.subtitulo("Já tem conta?"),
                        ft.TextButton(
                            content="Entrar",
                            on_click=lambda _: app.substituir("login"),
                            style=ft.ButtonStyle(color=t.VERDE_PRIMARIO),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=0,
                ),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=24, vertical=18),
        expand=True,
        bgcolor=t.FUNDO_CLARO,
    )
