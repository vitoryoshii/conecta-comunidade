"""Tela 2 — Cadastro.

Uma das três telas de autenticação; todas compartilham o andaime visual
`theme.tela_de_autenticacao` (foto de fundo, disco do logo, campos brancos).

A região é escolhida em dois passos — estado e depois cidade —, servidos por
`GET /localidades/...` a partir da base do IBGE.

Os dados pessoais (CPF, telefone e nascimento) são mascarados na digitação e
enviados só com dígitos: quem valida de verdade é o backend, que confere dígito
verificador, DDD e idade mínima. A checagem local existe para o usuário ver o
erro antes de enviar, não para substituir a do servidor.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import flet as ft

from mobile import mascaras
from mobile import theme as t

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

# Tipos de usuário aceitos pela API, com um rótulo amigável e um ícone.
TIPOS = [
    ("solicitante", "Preciso de ajuda", ft.Icons.PAN_TOOL_OUTLINED),
    ("doador", "Quero doar", ft.Icons.CARD_GIFTCARD_OUTLINED),
    ("voluntario", "Sou voluntário(a)", ft.Icons.DIVERSITY_3_OUTLINED),
    ("ong", "Represento uma ONG", ft.Icons.APARTMENT_OUTLINED),
]

# Exigência espelhada do backend (`dados_pessoais_service.IDADE_MINIMA`).
IDADE_MINIMA = 18

# Finalidade da coleta do CPF, exibida junto ao campo. A LGPD pede que a
# finalidade seja informada no momento em que o dado é solicitado.
FINALIDADE_DO_CPF = "Seu CPF é usado apenas para emissão de recibos de doação."

TEXTO_DO_CONSENTIMENTO = "Li e aceito os Termos de Uso e a Política de Privacidade"


def construir(app: App) -> ft.Control:
    """Formulário de criação de conta."""
    campo_nome = t.campo_claro("Seu nome completo", icone=t.ICONES["nome"])
    campo_email = t.campo_claro(
        "seu@email.com", icone=t.ICONES["email"], tipo_teclado=ft.KeyboardType.EMAIL
    )
    campo_senha = t.campo_claro("Mínimo 6 caracteres", senha=True, icone=t.ICONES["senha"])

    def formatar(campo: ft.TextField, mascara) -> None:
        """Reescreve o campo com a máscara aplicada e limpa o erro anterior."""
        campo.value = mascara(campo.value)
        campo.error = None
        app.page.update()

    campo_cpf = t.campo_claro(
        "000.000.000-00",
        icone=t.ICONES["cpf"],
        tipo_teclado=ft.KeyboardType.NUMBER,
        maximo=14,
        ao_mudar=lambda _: formatar(campo_cpf, mascaras.cpf),
    )
    campo_telefone = t.campo_claro(
        "(00) 00000-0000",
        icone=t.ICONES["telefone"],
        tipo_teclado=ft.KeyboardType.PHONE,
        maximo=15,
        ao_mudar=lambda _: formatar(campo_telefone, mascaras.telefone),
    )

    # A data vem de um seletor, e não de digitação livre: é o que elimina de vez
    # formato inválido e dia 31 de fevereiro. O campo exibe "dd/mm/aaaa" e guarda
    # o `date` real em `.data` — o slot que o Flet reserva para carga do controle
    # —, de modo que o valor mostrado e o valor enviado não podem divergir.
    campo_nascimento = t.campo_claro(
        "Selecione sua data de nascimento", icone=t.ICONES["nascimento"]
    )
    campo_nascimento.read_only = True

    def guardar_nascimento(evento: ft.ControlEvent) -> None:
        """Guarda a data escolhida no seletor e mostra no campo."""
        escolhida = evento.control.value
        if escolhida is None:
            return
        campo_nascimento.data = escolhida.date() if hasattr(escolhida, "date") else escolhida
        campo_nascimento.value = mascaras.data(campo_nascimento.data)
        campo_nascimento.error = None
        app.page.update()

    hoje = date.today()
    seletor_data = ft.DatePicker(
        first_date=date(hoje.year - 120, 1, 1),
        # O seletor já não deixa escolher quem não tem a idade mínima.
        last_date=date(hoje.year - IDADE_MINIMA, hoje.month, hoje.day),
        on_change=guardar_nascimento,
    )

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

    def validar(campo: ft.TextField, condicao: bool, mensagem: str) -> bool:
        """Marca o campo em vermelho quando a condição falha."""
        campo.error = None if condicao else mensagem
        return condicao

    def cadastrar(_: ft.ControlEvent) -> None:
        """Valida o formulário e cria a conta na API."""
        nome = campo_nome.value.strip()
        email = campo_email.value.strip()
        senha = campo_senha.value or ""
        cpf = mascaras.somente_digitos(campo_cpf.value)
        telefone = mascaras.somente_digitos(campo_telefone.value)

        # `all` sobre a lista inteira, e não encadeado: assim todos os campos
        # com problema acendem de uma vez, em vez de um por envio.
        valido = all(
            [
                validar(campo_nome, len(nome) >= 2, "Informe seu nome completo."),
                validar(campo_cpf, len(cpf) == 11, "O CPF precisa ter 11 dígitos."),
                validar(
                    campo_nascimento,
                    campo_nascimento.data is not None,
                    "Selecione sua data de nascimento.",
                ),
                validar(campo_email, "@" in email, "Informe um e-mail válido."),
                validar(campo_telefone, len(telefone) in (10, 11), "Informe DDD + número."),
                validar(campo_senha, len(senha) >= 6, "Mínimo de 6 caracteres."),
            ]
        )
        app.page.update()
        if not valido:
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
                    # Só dígitos: a máscara é coisa da tela.
                    "cpf": cpf,
                    "telefone": telefone,
                    "data_nascimento": campo_nascimento.data.isoformat(),
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

    botao_criar = t.botao_primario(
        "Criar conta",
        cadastrar,
        largura=t.LARGURA_FORMULARIO,
        cor=t.BRANCO,
        cor_texto=t.VERDE_ESCURO,
    )
    # Sem consentimento não há cadastro: o botão nasce desligado.
    botao_criar.disabled = True

    def alternar_consentimento(evento: ft.ControlEvent) -> None:
        """Libera o botão só quando os termos são aceitos."""
        botao_criar.disabled = not evento.control.value
        app.page.update()

    consentimento = ft.Checkbox(
        label=TEXTO_DO_CONSENTIMENTO,
        value=False,
        on_change=alternar_consentimento,
        label_style=ft.TextStyle(color=t.BRANCO, size=12),
        fill_color=t.BRANCO,
        check_color=t.VERDE_ESCURO,
    )

    return t.tela_de_autenticacao(
        [
            t.campo_rotulado("Nome completo", campo_nome),
            t.campo_rotulado("CPF", campo_cpf),
            t.ajuda_clara(FINALIDADE_DO_CPF, icone=t.ICONES["privacidade"]),
            t.campo_rotulado(
                "Data de nascimento",
                ft.Container(
                    content=campo_nascimento,
                    on_click=lambda _: app.page.show_dialog(seletor_data),
                ),
            ),
            t.campo_rotulado("E-mail", campo_email),
            t.campo_rotulado("Telefone / WhatsApp", campo_telefone),
            t.campo_rotulado("Senha", campo_senha),
            t.campo_rotulado("Como você quer participar?", seletor_tipo),
            t.campo_rotulado("Estado", seletor_estado),
            t.campo_rotulado("Cidade", seletor_cidade),
            t.ajuda_clara("Usamos sua região apenas para mostrar pedidos próximos."),
            ft.Container(height=6),
            consentimento,
            ft.Container(height=2),
            botao_criar,
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
