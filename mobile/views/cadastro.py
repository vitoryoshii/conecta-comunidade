"""Tela 2 — Cadastro.

Uma das três telas de autenticação; todas compartilham o andaime visual
`theme.tela_de_autenticacao` (foto de fundo, disco do logo, campos brancos).

A região é escolhida em dois passos — estado e depois cidade —, servidos por
`GET /localidades/...` a partir da base do IBGE.

Os dados pessoais (CPF, telefone e nascimento) são mascarados na digitação e
enviados só com dígitos: quem valida de verdade é o backend, que confere dígito
verificador, DDD e idade mínima. A checagem local existe para o usuário ver o
erro antes de enviar, não para substituir a do servidor.

O botão "Criar conta" nasce desligado e só liga quando o formulário inteiro
fecha — inclusive a confirmação de senha e o aceite dos termos. Abrir um dos
documentos legais não perde o que já foi digitado: a tela é reconstruída na
volta, e o rascunho guardado no `AppState` a repovoa.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any

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

# Exigências espelhadas do backend (`dados_pessoais_service.IDADE_MINIMA` e o
# `min_length` de `UsuarioCriar.senha`).
IDADE_MINIMA = 18
MINIMO_DE_SENHA = 6

# Data mais antiga oferecida no calendário. Nascimentos anteriores a 1900 não
# existem entre usuários vivos, e o limite evita uma rolagem infinita de anos.
PRIMEIRO_ANO = 1900

# Finalidade da coleta do CPF, exibida junto ao consentimento. A LGPD pede que a
# finalidade seja informada no momento em que o dado é solicitado.
FINALIDADE_DO_CPF = "Seu CPF é usado apenas para emissão de recibos de doação."

SENHAS_IGUAIS = "As senhas coincidem"
SENHAS_DIFERENTES = "As senhas não coincidem"


def construir(app: App) -> ft.Control:
    """Formulário de criação de conta."""
    rascunho: dict[str, Any] = dict(app.state.rascunho_cadastro)

    # --------------------------------------------------------------------- #
    # Campos
    # --------------------------------------------------------------------- #
    # Todo campo avisa a cada tecla: é o que mantém o botão "Criar conta"
    # acompanhando o estado real do formulário, e não só o do checkbox.
    campo_nome = t.campo_claro(
        "Seu nome completo", icone=t.ICONES["nome"], ao_mudar=lambda _: atualizar_botao()
    )
    campo_email = t.campo_claro(
        "seu@email.com",
        icone=t.ICONES["email"],
        tipo_teclado=ft.KeyboardType.EMAIL,
        ao_mudar=lambda _: atualizar_botao(),
    )

    def formatar(campo: ft.TextField, mascara) -> None:
        """Reescreve o campo com a máscara aplicada e limpa o erro anterior."""
        campo.value = mascara(campo.value)
        campo.error = None
        atualizar_botao()

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

    # --------------------------------------------------------------------- #
    # Data de nascimento
    # --------------------------------------------------------------------- #
    # A data vem de um seletor, e não de digitação livre: é o que elimina de vez
    # formato inválido e dia 31 de fevereiro. O campo exibe "dd/mm/aaaa" e guarda
    # o `date` real em `.data` — o slot que o Flet reserva para carga do controle
    # —, de modo que o valor mostrado e o valor enviado não podem divergir.
    hoje = date.today()
    # Última data que satisfaz a idade mínima: é o teto do calendário e também
    # onde ele abre. Um `DatePicker` sem `value` assume a data de hoje, que está
    # FORA deste intervalo — e um seletor cuja seleção inicial é inválida não
    # abre. Era esse o motivo de o calendário não aparecer no desktop.
    limite_de_idade = date(hoje.year - IDADE_MINIMA, hoje.month, hoje.day)

    def abrir_calendario(_: ft.ControlEvent | None = None) -> None:
        """Abre o seletor de data (no Flet 0.86, via `page.show_dialog`)."""
        app.page.show_dialog(seletor_data)

    campo_nascimento = t.campo_claro(
        "dd/mm/aaaa",
        icone=t.ICONES["nascimento"],
        somente_leitura=True,
        # O handler vai no próprio campo: um `Container` em volta nunca recebe o
        # clique, porque o `TextField` o consome antes.
        ao_clicar=abrir_calendario,
        # Segunda porta de entrada, e a mais visível: um botão de verdade dentro
        # do campo, que não depende do toque chegar ao TextField.
        sufixo=ft.IconButton(
            t.ICONES["calendario"],
            icon_color=t.VERDE_PRIMARIO,
            icon_size=t.ICONE_CAMPO,
            tooltip="Escolher a data",
            on_click=abrir_calendario,
        ),
    )

    def guardar_nascimento(evento: ft.ControlEvent) -> None:
        """Guarda a data escolhida no seletor e mostra no campo."""
        escolhida = evento.control.value
        if escolhida is None:
            return
        campo_nascimento.data = escolhida.date() if isinstance(escolhida, datetime) else escolhida
        campo_nascimento.value = mascaras.data(campo_nascimento.data)
        campo_nascimento.error = None
        atualizar_botao()

    nascimento_do_rascunho: date | None = rascunho.get("data_nascimento")
    seletor_data = ft.DatePicker(
        first_date=date(PRIMEIRO_ANO, 1, 1),
        # O seletor já não deixa escolher quem não tem a idade mínima.
        last_date=limite_de_idade,
        # Seleção inicial e "hoje" do calendário, ambas dentro do intervalo.
        value=nascimento_do_rascunho or limite_de_idade,
        current_date=limite_de_idade,
        # Começar pelo ano poupa a rolagem de mais de mil meses até 1900.
        date_picker_mode=ft.DatePickerMode.YEAR,
        help_text="Sua data de nascimento",
        cancel_text="Cancelar",
        confirm_text="Confirmar",
        on_change=guardar_nascimento,
    )

    # --------------------------------------------------------------------- #
    # Senha e confirmação
    # --------------------------------------------------------------------- #
    status_da_senha = ft.Container(visible=False)

    def conferir_senhas(_: ft.ControlEvent | None = None) -> None:
        """Feedback ao vivo da confirmação, a cada tecla digitada."""
        senha = campo_senha.value or ""
        confirmacao = campo_confirmacao.value or ""

        if not confirmacao:
            # Nada dito antes de a pessoa começar a confirmar: um "não coincide"
            # com o campo vazio seria uma bronca por algo que ela ainda vai fazer.
            status_da_senha.visible = False
        else:
            coincidem = confirmacao == senha and len(senha) >= MINIMO_DE_SENHA
            status_da_senha.visible = True
            status_da_senha.content = t.status_claro(
                SENHAS_IGUAIS if coincidem else SENHAS_DIFERENTES, ok=coincidem
            )
            if coincidem:
                campo_confirmacao.error = None

        atualizar_botao()

    campo_senha = t.campo_claro(
        "Mínimo 6 caracteres",
        senha=True,
        icone=t.ICONES["senha"],
        ao_mudar=conferir_senhas,
    )
    campo_confirmacao = t.campo_claro(
        "Repita a senha",
        senha=True,
        icone=t.ICONES["confirmar_senha"],
        ao_mudar=conferir_senhas,
    )

    # --------------------------------------------------------------------- #
    # Participação e região
    # --------------------------------------------------------------------- #
    seletor_tipo = t.dropdown_claro(
        [
            ft.DropdownOption(key=chave, text=rotulo, leading_icon=icone)
            for chave, rotulo, icone in TIPOS
        ],
        valor=rascunho.get("tipo") or "solicitante",
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
        ao_selecionar=lambda _: atualizar_botao(),
    )

    # Coordenadas da cidade escolhida, guardadas ao carregar a lista: o seletor
    # só devolve o nome, e é a partir delas que o usuário nasce no lugar certo
    # do mapa em vez de em (0, 0).
    coordenadas: dict[str, tuple[float, float]] = {}

    def preencher_cidades(sigla: str | None) -> None:
        """Busca os municípios da UF e (re)popula o seletor de cidade."""
        coordenadas.clear()
        cidades = app.executar(lambda: app.api.listar_cidades(sigla)) if sigla else None

        if cidades is None:
            seletor_cidade.options = []
            seletor_cidade.disabled = True
            seletor_cidade.hint_text = "Escolha o estado primeiro"
            return

        coordenadas.update({c["nome"]: (c["lat"], c["lng"]) for c in cidades})
        seletor_cidade.options = [ft.DropdownOption(key=c["nome"], text=c["nome"]) for c in cidades]
        seletor_cidade.disabled = False
        seletor_cidade.hint_text = "Digite para buscar"

    def carregar_cidades(_: ft.ControlEvent) -> None:
        """Preenche e habilita o seletor de cidade para a UF escolhida."""
        seletor_cidade.value = None
        preencher_cidades(seletor_estado.value)
        atualizar_botao()

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

    # --------------------------------------------------------------------- #
    # Consentimento e envio
    # --------------------------------------------------------------------- #
    def guardar_rascunho() -> None:
        """Salva o formulário antes de abrir outra tela."""
        app.state.guardar_rascunho(
            {
                "nome": campo_nome.value,
                "cpf": campo_cpf.value,
                "email": campo_email.value,
                "telefone": campo_telefone.value,
                "senha": campo_senha.value,
                "confirmacao": campo_confirmacao.value,
                "data_nascimento": campo_nascimento.data,
                "tipo": seletor_tipo.value,
                "estado": seletor_estado.value,
                "cidade": seletor_cidade.value,
                "aceite": consentimento.value,
            }
        )

    def abrir_documento(chave: str) -> None:
        """Abre um documento legal sem perder o que já foi preenchido."""
        guardar_rascunho()
        app.navegar("documento_legal", documento=chave)

    def sair_do_cadastro(ir: str | None = None) -> None:
        """Abandona o fluxo: o rascunho (com a senha) não sobrevive à saída."""
        app.state.limpar_rascunho()
        if ir is None:
            app.voltar()
        else:
            app.substituir(ir)

    def formulario_completo() -> bool:
        """Todos os campos obrigatórios preenchidos e coerentes entre si."""
        senha = campo_senha.value or ""
        return all(
            [
                len((campo_nome.value or "").strip()) >= 2,
                len(mascaras.somente_digitos(campo_cpf.value)) == 11,
                campo_nascimento.data is not None,
                "@" in (campo_email.value or ""),
                len(mascaras.somente_digitos(campo_telefone.value)) in (10, 11),
                len(senha) >= MINIMO_DE_SENHA,
                (campo_confirmacao.value or "") == senha,
                bool(seletor_estado.value),
                bool(seletor_cidade.value),
                bool(consentimento.value),
            ]
        )

    def atualizar_botao(_: ft.ControlEvent | None = None) -> None:
        """Liga o botão só quando o formulário inteiro fecha."""
        botao_criar.disabled = not formulario_completo()
        app.page.update()

    def validar(campo: ft.TextField, condicao: bool, mensagem: str) -> bool:
        """Marca o campo em vermelho quando a condição falha."""
        campo.error = None if condicao else mensagem
        return condicao

    def cadastrar(_: ft.ControlEvent) -> None:
        """Valida o formulário e cria a conta na API."""
        nome = (campo_nome.value or "").strip()
        email = (campo_email.value or "").strip()
        senha = campo_senha.value or ""
        confirmacao = campo_confirmacao.value or ""
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
                validar(campo_senha, len(senha) >= MINIMO_DE_SENHA, "Mínimo de 6 caracteres."),
                validar(campo_confirmacao, confirmacao == senha, SENHAS_DIFERENTES),
            ]
        )
        app.page.update()
        if not valido:
            return

        # O aceite é exigido pelo backend (422 sem ele); barrar aqui evita a ida
        # à API só para ouvir o que a tela já sabe.
        if not consentimento.value:
            app.aviso("Aceite os Termos de Uso e a Política de Privacidade.", erro=True)
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
                    "aceite_termos": True,
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
        app.state.limpar_rascunho()
        app.aviso("Conta criada! Bem-vindo(a) ao Conecta Comunidade.")
        app.reiniciar("home")

    botao_criar = t.botao_primario(
        "Criar conta",
        cadastrar,
        largura=t.LARGURA_FORMULARIO,
        cor=t.BRANCO,
        cor_texto=t.VERDE_ESCURO,
    )
    # Sem consentimento (e sem o resto do formulário) não há cadastro.
    botao_criar.disabled = True

    def link_do_documento(texto: str, chave: str) -> ft.TextSpan:
        """Trecho clicável do consentimento que abre um documento legal."""
        return ft.TextSpan(
            texto,
            style=ft.TextStyle(
                color=t.AMBAR_CLARO,
                weight=ft.FontWeight.W_600,
                decoration=ft.TextDecoration.UNDERLINE,
                decoration_color=t.AMBAR_CLARO,
            ),
            on_click=lambda _, chave=chave: abrir_documento(chave),
        )

    consentimento = ft.Checkbox(
        # O rótulo é um `Text` com spans, e não uma string: é o que torna
        # "Termos de Uso" e "Política de Privacidade" clicáveis dentro da frase.
        label=ft.Text(
            spans=[
                ft.TextSpan("Li e aceito os "),
                link_do_documento("Termos de Uso", "termos"),
                ft.TextSpan(" e a "),
                link_do_documento("Política de Privacidade", "privacidade"),
            ],
            size=12,
            color=t.BRANCO,
        ),
        value=False,
        on_change=atualizar_botao,
        fill_color=t.BRANCO,
        check_color=t.VERDE_ESCURO,
    )

    # --------------------------------------------------------------------- #
    # Rascunho: repovoa a tela na volta de um documento legal
    # --------------------------------------------------------------------- #
    if rascunho:
        campo_nome.value = rascunho.get("nome") or ""
        campo_cpf.value = rascunho.get("cpf") or ""
        campo_email.value = rascunho.get("email") or ""
        campo_telefone.value = rascunho.get("telefone") or ""
        campo_senha.value = rascunho.get("senha") or ""
        campo_confirmacao.value = rascunho.get("confirmacao") or ""
        consentimento.value = bool(rascunho.get("aceite"))

        if nascimento_do_rascunho is not None:
            campo_nascimento.data = nascimento_do_rascunho
            campo_nascimento.value = mascaras.data(nascimento_do_rascunho)

        # A cidade precisa da lista da UF de volta — é ela que traz também as
        # coordenadas usadas no envio.
        if rascunho.get("estado"):
            seletor_estado.value = rascunho["estado"]
            preencher_cidades(rascunho["estado"])
            seletor_cidade.value = rascunho.get("cidade")

        conferir_senhas()
        botao_criar.disabled = not formulario_completo()

    return t.tela_de_autenticacao(
        [
            t.campo_rotulado("Nome completo", campo_nome),
            t.campo_rotulado("CPF", campo_cpf),
            t.campo_rotulado("Data de nascimento", campo_nascimento),
            t.campo_rotulado("E-mail", campo_email),
            t.campo_rotulado("Telefone / WhatsApp", campo_telefone),
            t.campo_rotulado("Senha", campo_senha),
            t.campo_rotulado("Confirmar senha", campo_confirmacao),
            status_da_senha,
            t.campo_rotulado("Como você quer participar?", seletor_tipo),
            t.campo_rotulado("Estado", seletor_estado),
            t.campo_rotulado("Cidade", seletor_cidade),
            t.ajuda_clara("Usamos sua região apenas para mostrar pedidos próximos."),
            t.ajuda_clara(FINALIDADE_DO_CPF, icone=t.ICONES["privacidade"]),
            ft.Container(height=6),
            consentimento,
            ft.Container(height=2),
            botao_criar,
            ft.Row(
                [
                    ft.Text("Já tem conta?", size=12, color=t.MENTA_CLARA),
                    t.link_claro("Entrar", lambda _: sair_do_cadastro("login")),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=0,
            ),
        ],
        on_voltar=lambda _: sair_do_cadastro(),
        cabecalho=(
            "Criar sua conta",
            "Leva menos de um minuto. Seus dados ficam protegidos.",
        ),
    )
