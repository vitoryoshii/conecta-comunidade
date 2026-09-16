"""Tela 2 — Cadastro.

Uma das três telas de autenticação; todas compartilham o andaime visual
`theme.tela_de_autenticacao` (foto de fundo, disco do logo, campos brancos).

A região é escolhida em dois passos — estado e depois cidade —, servidos por
`GET /localidades/...` a partir da base do IBGE.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from mobile import theme as t

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

# Tipos de usuário aceitos pela API, com um rótulo amigável e um ícone.
TIPOS = [
    ("solicitante", "Preciso de ajuda", t.ICONES["preciso_de_ajuda"]),
    ("doador", "Quero doar", t.ICONES["doar"]),
    ("voluntario", "Sou voluntário(a)", t.ICONES["voluntariado"]),
    ("ong", "Represento uma ONG", t.ICONES["ong"]),
]


def construir(app: App) -> ft.Control:
    """Formulário de criação de conta."""
    campo_nome = t.campo_claro("Seu nome completo", icone=t.ICONES["nome"])
    campo_email = t.campo_claro(
        "seu@email.com", icone=t.ICONES["email"], tipo_teclado=ft.KeyboardType.EMAIL
    )
    campo_senha = t.campo_claro("Mínimo 6 caracteres", senha=True, icone=t.ICONES["senha"])

    seletor_tipo = t.dropdown_claro(
        [
            ft.DropdownOption(key=chave, text=rotulo, leading_icon=icone)
            for chave, rotulo, icone in TIPOS
        ],
        valor="solicitante",
        icone=t.ICONES["participacao"],
    )

    # A cidade só abre depois do estado: são 5.571 municípios no país, e a lista
    # de um estado só faz sentido depois de saber qual é.
    seletor_cidade = t.dropdown_claro(
        [],
        dica="Escolha o estado primeiro",
        icone=t.ICONES["cidade"],
        desabilitado=True,
        filtravel=True,
    )

    # Coordenadas da cidade escolhida, guardadas ao carregar a lista: o seletor
    # só devolve o nome, e é a partir delas que o usuário nasce no lugar certo
    # do mapa em vez de em (0, 0).
    coordenadas: dict[str, tuple[float, float]] = {}

    def carregar_cidades(_: ft.ControlEvent) -> None:
        """Preenche e habilita o seletor de cidade para a UF escolhida."""
        sigla = seletor_estado.value
        seletor_cidade.value = None
        coordenadas.clear()

        cidades = app.executar(lambda: app.api.listar_cidades(sigla)) if sigla else None
        if cidades is None:
            seletor_cidade.options = []
            seletor_cidade.disabled = True
            seletor_cidade.hint_text = "Escolha o estado primeiro"
        else:
            coordenadas.update({c["nome"]: (c["lat"], c["lng"]) for c in cidades})
            seletor_cidade.options = [
                ft.DropdownOption(key=c["nome"], text=c["nome"]) for c in cidades
            ]
            seletor_cidade.disabled = False
            seletor_cidade.hint_text = "Digite para buscar"

        app.page.update()

    # A lista de estados é curta e não muda: vem junto com a montagem da tela.
    # Se a API estiver fora, o erro sobe para `App.renderizar`, que troca a tela
    # pelo aviso de "sem conexão" — melhor do que um seletor vazio sem explicação.
    estados = app.api.listar_estados()
    seletor_estado = t.dropdown_claro(
        [ft.DropdownOption(key=e["sigla"], text=e["nome"]) for e in estados],
        dica="Selecione seu estado",
        icone=t.ICONES["estado"],
        filtravel=True,
        ao_selecionar=carregar_cidades,
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
        if not seletor_estado.value:
            app.aviso("Escolha o seu estado.", erro=True)
            return
        if not seletor_cidade.value:
            app.aviso("Escolha a sua cidade.", erro=True)
            return

        latitude, longitude = coordenadas.get(seletor_cidade.value, (0.0, 0.0))
        resposta = app.executar(
            lambda: app.api.registrar(
                {
                    "nome": nome,
                    "email": email,
                    "senha": senha,
                    "tipo": seletor_tipo.value,
                    "estado": seletor_estado.value,
                    "cidade": seletor_cidade.value,
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
            t.campo_rotulado("Estado", seletor_estado),
            t.campo_rotulado("Cidade", seletor_cidade),
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
