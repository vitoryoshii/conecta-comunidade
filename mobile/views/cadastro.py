"""Tela 2 — Cadastro.

Uma das três telas de autenticação; todas compartilham o andaime visual
`theme.tela_de_autenticacao` (foto de fundo, disco do logo, campos brancos).
"""

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
    campo_nome = t.campo_claro("Seu nome completo")
    campo_email = t.campo_claro("seu@email.com", tipo_teclado=ft.KeyboardType.EMAIL)
    campo_senha = t.campo_claro("Mínimo 6 caracteres", senha=True)

    seletor_tipo = t.dropdown_claro(
        [
            ft.DropdownOption(key=chave, text=rotulo, leading_icon=icone)
            for chave, rotulo, icone in TIPOS
        ],
        valor="solicitante",
    )

    seletor_local = t.dropdown_claro(
        [ft.DropdownOption(key=nome, text=nome) for nome, _, _ in LOCALIDADES],
        valor=LOCALIDADES[0][0],
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

    return t.tela_de_autenticacao(
        [
            t.campo_rotulado("Nome completo", campo_nome),
            t.campo_rotulado("E-mail", campo_email),
            t.campo_rotulado("Senha", campo_senha),
            t.campo_rotulado("Como você quer participar?", seletor_tipo),
            t.campo_rotulado("Onde você está?", seletor_local),
            t.ajuda_clara("Usamos sua região apenas para mostrar pedidos próximos."),
            ft.Container(height=6),
            t.botao_primario(
                "Criar conta",
                cadastrar,
                largura=t.LARGURA_FORMULARIO,
                cor=t.BRANCO,
                cor_texto=t.VERDE_ESCURO,
            ),
            ft.Row(
                [
                    ft.Text("Já tem conta?", size=12, color=t.MENTA_CLARA),
                    t.link_claro("Entrar", lambda _: app.substituir("login")),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=0,
            ),
        ],
        on_voltar=app.voltar,
        cabecalho=(
            "Criar sua conta",
            "Leva menos de um minuto. Seus dados ficam protegidos.",
        ),
    )
