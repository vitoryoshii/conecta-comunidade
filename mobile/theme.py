"""
Identidade visual do Conecta Comunidade.

Concentra a paleta oficial, os estilos de texto e as fábricas de componentes
reutilizados pelas telas (botões, campos, cartões e badges). Nenhuma view define
cor ou espaçamento "na mão": tudo sai daqui, o que mantém o app coerente e
facilita ajustar o visual em um só lugar.
"""

import flet as ft

# --------------------------------------------------------------------------- #
# Paleta oficial do produto
# --------------------------------------------------------------------------- #
TEAL = "#2FD3C0"                # acento tecnológico da identidade v2
VERDE_PRIMARIO = "#1FA96C"      # ações principais, identidade da marca
VERDE_ESCURO = "#0E6B42"        # estados pressionados, gradientes
VERDE_PROFUNDO = "#0B5A3A"      # fim do gradiente do banner e do FAB
VERDE_BANNER = "#127C58"        # início do gradiente do banner
AZUL_INSTITUCIONAL = "#0E2A47"  # navy da marca: pin de ONG, avatar institucional
FUNDO_CLARO = "#FBFCFB"         # fundo das telas
FUNDO_MOLDURA = "#E4EAE7"       # laterais vazias da janela larga no desktop:
                                # um degrau abaixo do FUNDO_CLARO, só o
                                # suficiente para a coluna central se ler como
                                # o app. Invisível no celular.
URGENCIA = "#E23B3B"            # alertas, urgência alta, modo emergência
# Par de texto do padrão premium. `TEXTO_FORTE` é um quase-preto esverdeado, e
# não o navy: sobre o fundo levemente verde das telas ele assenta, enquanto o
# azul vibra. O navy continua existindo, mas como acento institucional.
TEXTO_FORTE = "#122C1E"         # títulos e textos de destaque
TEXTO_SECUNDARIO = "#9AA5A0"    # legendas, metadados, textos de apoio
TEXTO_INATIVO = "#B0BAB5"       # itens não selecionados da navegação

# Tons derivados, criados a partir da paleta para dar profundidade à interface.
BRANCO = "#FFFFFF"
TRANSPARENTE = "#00000000"      # bordas apagadas, sem recorrer a ft.Colors
MENTA = "#8FE3AE"
VERDE_SUAVE = "#E8F8F0"         # fundo de chips e destaques discretos
BORDA = "#E1E8E4"               # divisórias e contornos de cartões
AMARELO_ATENCAO = "#F5A623"     # urgência média e pontos de retirada
CINZA_CLARO = "#EEF2F0"         # fundo de campos e superfícies neutras
MENTA_CLARA = "#D9F2E4"         # textos de apoio sobre fundo escuro/foto
AMBAR_CLARO = "#FFDC8C"         # links de destaque sobre fundo escuro/foto
VERDE_CONFIRMA = "#7BE8A5"      # confirmação ("as senhas coincidem") sobre foto
VERMELHO_CLARO = "#FFB4AB"      # erro sobre fundo escuro/foto — o URGENCIA
                                # some na foto, escuro demais para esse fundo

# Cores por nível de urgência, usadas nos badges dos cartões.
CORES_URGENCIA = {
    "alta": URGENCIA,
    "media": AMARELO_ATENCAO,
    "baixa": VERDE_PRIMARIO,
}

ROTULOS_URGENCIA = {
    "alta": "Urgente",
    "media": "Média",
    "baixa": "Baixa",
}

# --------------------------------------------------------------------------- #
# Ícones
# --------------------------------------------------------------------------- #
# Regra da casa: todo ícone é **outlined**; quando a família não tem outlined,
# usamos a variante rounded. Nunca misturar preenchido e contornado na mesma
# tela — a única exceção é a navegação inferior, onde o item ativo usa a versão
# cheia da MESMA família justamente para sinalizar seleção.
#
# As telas referenciam por nome semântico (`t.ICONES["doacoes"]`) em vez de
# espalhar `ft.Icons.X`: trocar um ícone do produto passa a ser uma edição só.
ICONES = {
    # Pilares e ações do produto
    "doacoes": ft.Icons.VOLUNTEER_ACTIVISM_OUTLINED,
    "voluntariado": ft.Icons.DIVERSITY_3_OUTLINED,
    # EMERGENCY, e não CRISIS_ALERT: o desenho do crisis_alert é um círculo
    # com traço vertical e arcos, que se lê como botão de "power".
    "emergencias": ft.Icons.EMERGENCY_OUTLINED,
    "preciso_de_ajuda": ft.Icons.PAN_TOOL_OUTLINED,
    "quero_ajudar": ft.Icons.VOLUNTEER_ACTIVISM_OUTLINED,
    "doar": ft.Icons.CARD_GIFTCARD_OUTLINED,
    "ong": ft.Icons.APARTMENT_OUTLINED,
    "ponto_retirada": ft.Icons.STOREFRONT_OUTLINED,
    "entrega": ft.Icons.LOCAL_SHIPPING_OUTLINED,
    "pedido": ft.Icons.ASSIGNMENT_OUTLINED,
    "oferta": ft.Icons.INVENTORY_2_OUTLINED,

    # Campos de formulário
    "nome": ft.Icons.PERSON_OUTLINE_ROUNDED,
    "cpf": ft.Icons.BADGE_OUTLINED,
    "telefone": ft.Icons.PHONE_OUTLINED,
    "nascimento": ft.Icons.CAKE_OUTLINED,
    "calendario": ft.Icons.CALENDAR_MONTH_ROUNDED,
    "privacidade": ft.Icons.PRIVACY_TIP_OUTLINED,
    "documento": ft.Icons.DESCRIPTION_OUTLINED,
    "email": ft.Icons.MAIL_OUTLINE_ROUNDED,
    "senha": ft.Icons.LOCK_OUTLINE_ROUNDED,
    "confirmar_senha": ft.Icons.LOCK_RESET_ROUNDED,
    # Par de confirmação/erro do feedback ao vivo dos formulários.
    "confere": ft.Icons.CHECK_CIRCLE_ROUNDED,
    "nao_confere": ft.Icons.CANCEL_ROUNDED,
    "participacao": ft.Icons.HANDSHAKE_OUTLINED,
    "estado": ft.Icons.MAP_OUTLINED,
    "cidade": ft.Icons.LOCATION_CITY_OUTLINED,
    "titulo": ft.Icons.TITLE_ROUNDED,
    "descricao": ft.Icons.NOTES_ROUNDED,
    "quantidade": ft.Icons.NUMBERS_ROUNDED,
    "categoria": ft.Icons.LABEL_OUTLINE_ROUNDED,
    "categoria_generica": ft.Icons.CATEGORY_OUTLINED,
    "imagem": ft.Icons.IMAGE_OUTLINED,

    # Navegação e ações
    "voltar": ft.Icons.ARROW_BACK_ROUNDED,
    "avancar": ft.Icons.ARROW_FORWARD_ROUNDED,
    "detalhe": ft.Icons.CHEVRON_RIGHT_ROUNDED,
    "buscar": ft.Icons.SEARCH_ROUNDED,
    "filtrar": ft.Icons.TUNE_ROUNDED,
    "enviar": ft.Icons.SEND_OUTLINED,
    "adicionar": ft.Icons.ADD_ROUNDED,
    "fechar": ft.Icons.CLOSE_ROUNDED,
    "recarregar": ft.Icons.REFRESH_ROUNDED,
    "compartilhar": ft.Icons.SHARE_OUTLINED,
    "configuracoes": ft.Icons.SETTINGS_OUTLINED,
    "sair": ft.Icons.LOGOUT_ROUNDED,
    "entrar": ft.Icons.LOGIN_ROUNDED,
    "criar_conta": ft.Icons.PERSON_ADD_ALT_1_OUTLINED,
    "localizar": ft.Icons.MY_LOCATION_OUTLINED,

    # Estado e feedback
    "info": ft.Icons.INFO_OUTLINE_ROUNDED,
    "ajuda": ft.Icons.HELP_OUTLINE_ROUNDED,
    "sucesso": ft.Icons.CHECK_CIRCLE_OUTLINE,
    "concluido": ft.Icons.TASK_ALT_ROUNDED,
    "erro": ft.Icons.ERROR_OUTLINE_ROUNDED,
    "urgente": ft.Icons.PRIORITY_HIGH_ROUNDED,
    "sem_conexao": ft.Icons.CLOUD_OFF_ROUNDED,
    "vazio": ft.Icons.INBOX_OUTLINED,
    "sem_resultado": ft.Icons.SEARCH_OFF_ROUNDED,
    "verificada": ft.Icons.VERIFIED_OUTLINED,
    "agenda": ft.Icons.EVENT_AVAILABLE_OUTLINED,
    "horario": ft.Icons.SCHEDULE_OUTLINED,
    "data": ft.Icons.CALENDAR_TODAY_OUTLINED,
    "local": ft.Icons.PLACE_OUTLINED,
    "pessoas": ft.Icons.GROUP_OUTLINED,
    "conversa": ft.Icons.CHAT_BUBBLE_OUTLINE,
    "conversas": ft.Icons.FORUM_OUTLINED,
    "demonstracao": ft.Icons.SCIENCE_OUTLINED,
}

# Tamanhos por contexto — nada de valor solto no meio da tela.
ICONE_CAMPO = 20      # prefixo de campo, rótulo, linha de apoio
ICONE_ACAO = 24       # botões, navegação, barras
ICONE_DESTAQUE = 28   # cartões, categorias, cabeçalhos

# Cores dos pins do mapa, por tipo de ponto.
CORES_MAPA = {
    "ajuda": URGENCIA,
    "oferecendo": VERDE_PRIMARIO,
    "ong": AZUL_INSTITUCIONAL,
    "ponto_retirada": AMARELO_ATENCAO,
}

ICONES_MAPA = {
    "ajuda": ICONES["preciso_de_ajuda"],
    "oferecendo": ICONES["doacoes"],
    "ong": ICONES["ong"],
    "ponto_retirada": ICONES["ponto_retirada"],
}

ROTULOS_MAPA = {
    "ajuda": "Precisa de ajuda",
    "oferecendo": "Oferecendo",
    "ong": "ONGs",
    "ponto_retirada": "Pontos de retirada",
}

# Arquivos da marca servidos pelo `assets_dir` do Flet.
# Logo único do app (coração âmbar + mão verde, sem o quadrado de fundo),
# exibido dentro do disco branco em splash, login, cadastro e recuperação.
LOGO_APP = "brand/logo/logo-icon.svg"
# Foto de fundo compartilhada pela abertura e pelas telas de autenticação. A
# imagem já vem da identidade visual com o overlay verde embutido: nenhuma tela
# deve empilhar outra camada de cor por cima dela.
FOTO_DE_FUNDO = "brand/img/login-bg.jpg"

# --------------------------------------------------------------------------- #
# Sombras
# --------------------------------------------------------------------------- #
# É a sombra — e não o traço — que separa as superfícies no padrão premium.
# Uma borda cinza de 1px recorta o cartão e "achata" a tela; a sombra curta e
# clara levanta a superfície sem sujar o fundo. Por isso `cartao()` não desenha
# mais borda: quem precisa marcar um estado (uma emergência) passa `borda`.
#
# São dataclasses do Flet, não controles, então a MESMA instância pode ser
# reaproveitada por quantos containers precisarem.
SOMBRA_CARD = ft.BoxShadow(blur_radius=16, color="#0D000000", offset=ft.Offset(0, 3))
SOMBRA_FLUTUANTE = ft.BoxShadow(blur_radius=22, color="#470B5A3A", offset=ft.Offset(0, 8))
# Offset negativo: a nav bar projeta a sombra para CIMA, sobre o conteúdo.
SOMBRA_NAV = ft.BoxShadow(blur_radius=16, color="#0D000000", offset=ft.Offset(0, -2))

# Raio padrão de arredondamento e espaçamento base das telas.
RAIO_CARD = 18        # cartões e superfícies grandes
RAIO_BOTAO = 14       # botões, campos e quadradinhos de ícone
RAIO_CATEGORIA = 18   # quadrados das categorias
RAIO = RAIO_CARD      # nome antigo, mantido para as telas ainda não redesenhadas
ESPACO = 16

# --------------------------------------------------------------------------- #
# Tipografia
# --------------------------------------------------------------------------- #
TAMANHO_TITULO_SECAO = 16.5
TAMANHO_TITULO_CARD = 15
TAMANHO_META = 11.5

# Largura útil do formulário nas telas sobre foto: a janela de demonstração
# tem 430px e a tela reserva 36px de padding de cada lado.
LARGURA_FORMULARIO = 358

# Disco branco do topo das telas: 140px, com o logo ocupando ~104px dele.
LADO_DO_DISCO = 140
PROPORCAO_DO_LOGO = 0.74

# --------------------------------------------------------------------------- #
# Cores por categoria (tom sobre tom)
# --------------------------------------------------------------------------- #
# Cada categoria tem um par (cor do ícone, fundo bem claro da MESMA cor) — é o
# tom sobre tom que dá o ar premium à grade e aos cartões.
#
# A chave é o nome do ícone vindo da API (`categoria["icone"]`, e
# `solicitacao["categoria_icone"]` nos cartões), e não a posição na lista: assim
# "Água" é azul na Home e no cartão da solicitação, mesmo que a API devolva as
# categorias em outra ordem. Categoria nova cai em `COR_CATEGORIA_PADRAO`.
CATEGORIA_CORES = {
    "water_drop": ("#2F9BD3", "#E6F4FB"),       # Água
    "restaurant": ("#D8712F", "#FDEEE6"),       # Alimentos
    "checkroom": ("#1FA96C", "#E4F7EE"),        # Roupas
    "home": ("#2F6FD3", "#EAF1FB"),             # Abrigo
    "medical_services": ("#E23B3B", "#FDECEC"), # Medicamentos
    "school": ("#7A5AD8", "#F0ECFB"),           # Material Escolar
    "chair": ("#1FA96C", "#E4F7EE"),            # Móveis
    "category": ("#6B7B72", "#EEF1EF"),         # Outros
}

COR_CATEGORIA_PADRAO = ("#6B7B72", "#EEF1EF")


def cores_da_categoria(icone: str | None) -> tuple[str, str]:
    """Par (cor do ícone, cor de fundo) da categoria, pelo nome do ícone."""
    return CATEGORIA_CORES.get(icone or "", COR_CATEGORIA_PADRAO)


# --------------------------------------------------------------------------- #
# Tema global do Flet
# --------------------------------------------------------------------------- #
def tema_do_app() -> ft.Theme:
    """Tema Material aplicado à página inteira."""
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=VERDE_PRIMARIO,
            on_primary=BRANCO,
            secondary=AZUL_INSTITUCIONAL,
            surface=BRANCO,
            error=URGENCIA,
        ),
        font_family="Segoe UI",
    )


# --------------------------------------------------------------------------- #
# Textos
# --------------------------------------------------------------------------- #
def titulo(texto: str, tamanho: int = 22, cor: str = TEXTO_FORTE) -> ft.Text:
    """Título de tela ou de seção.

    O `letter_spacing` levemente negativo é o que faz um título bold parecer
    desenhado, e não apenas "engrossado": as letras fecham entre si e o bloco de
    texto ganha peso sem precisar de mais tamanho.
    """
    return ft.Text(
        texto,
        size=tamanho,
        weight=ft.FontWeight.BOLD,
        color=cor,
        style=ft.TextStyle(letter_spacing=-0.4),
    )


def titulo_secao(texto: str, cor: str = TEXTO_FORTE) -> ft.Text:
    """Título das seções internas ("Categorias", "Meu impacto"...)."""
    return titulo(texto, TAMANHO_TITULO_SECAO, cor)


def titulo_cartao(texto: str, cor: str = TEXTO_FORTE, **kwargs) -> ft.Text:
    """Título de um item de lista, dentro de um cartão."""
    return ft.Text(
        texto,
        size=TAMANHO_TITULO_CARD,
        weight=ft.FontWeight.W_700,
        color=cor,
        style=ft.TextStyle(letter_spacing=-0.2),
        **kwargs,
    )


def meta(texto: str, cor: str = TEXTO_SECUNDARIO, **kwargs) -> ft.Text:
    """Metadado de cartão: distância, tempo, contagem."""
    return ft.Text(texto, size=TAMANHO_META, color=cor, **kwargs)


def subtitulo(texto: str, tamanho: int = 13, cor: str = TEXTO_SECUNDARIO) -> ft.Text:
    """Texto de apoio, usado em legendas e metadados."""
    return ft.Text(texto, size=tamanho, color=cor)


def corpo(texto: str, tamanho: int = 14, cor: str = TEXTO_FORTE, **kwargs) -> ft.Text:
    """Texto corrido padrão."""
    return ft.Text(texto, size=tamanho, color=cor, **kwargs)


# --------------------------------------------------------------------------- #
# Botões
# --------------------------------------------------------------------------- #
def botao_primario(
    texto: str,
    on_click,
    icone: ft.IconData | None = None,
    largura: int | None = None,
    cor: str = VERDE_PRIMARIO,
    cor_texto: str = BRANCO,
) -> ft.FilledButton:
    """Botão de ação principal (verde, cantos arredondados).

    Sobre foto as telas invertem as cores (`cor=BRANCO`, `cor_texto=VERDE_ESCURO`)
    em vez de montar outro botão.
    """
    return ft.FilledButton(
        content=texto,
        icon=icone,
        on_click=on_click,
        bgcolor=cor,
        color=cor_texto,
        width=largura,
        height=50,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=RAIO_BOTAO),
            # A elevação é o equivalente da `SOMBRA_FLUTUANTE` em um botão do
            # Material: o verde principal passa a flutuar sobre a tela.
            elevation=6,
            shadow_color=VERDE_PROFUNDO,
        ),
    )


def botao_secundario(
    texto: str,
    on_click,
    icone: ft.IconData | None = None,
    largura: int | None = None,
    cor: str = VERDE_PRIMARIO,
) -> ft.OutlinedButton:
    """Botão de ação secundária (contorno, fundo transparente)."""
    return ft.OutlinedButton(
        content=texto,
        icon=icone,
        on_click=on_click,
        width=largura,
        height=50,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=RAIO_BOTAO),
            color=cor,
            side=ft.BorderSide(width=1.4, color=cor),
        ),
    )


# --------------------------------------------------------------------------- #
# Campos de formulário
# --------------------------------------------------------------------------- #
def campo(
    rotulo: str,
    valor: str = "",
    senha: bool = False,
    multilinha: bool = False,
    icone: ft.IconData | None = None,
    dica: str | None = None,
    tipo_teclado: ft.KeyboardType = ft.KeyboardType.TEXT,
) -> ft.TextField:
    """Campo de texto no estilo do app (preenchido, sem borda dura)."""
    return ft.TextField(
        label=rotulo,
        value=valor,
        hint_text=dica,
        password=senha,
        can_reveal_password=senha,
        multiline=multilinha,
        min_lines=3 if multilinha else None,
        max_lines=5 if multilinha else 1,
        prefix_icon=icone,
        # Todo ícone de campo no mesmo tamanho, em qualquer tela.
        prefix_icon_size_constraints=ft.BoxConstraints(
            min_width=ICONE_CAMPO, min_height=ICONE_CAMPO
        ),
        keyboard_type=tipo_teclado,
        filled=True,
        fill_color=BRANCO,
        border_radius=12,
        border_color=BORDA,
        focused_border_color=VERDE_PRIMARIO,
        color=TEXTO_FORTE,
        label_style=ft.TextStyle(color=TEXTO_SECUNDARIO, size=13),
    )


# --------------------------------------------------------------------------- #
# Telas sobre foto (login e recuperação de senha)
# --------------------------------------------------------------------------- #
# As imagens de fundo já vêm da identidade visual com o overlay verde aplicado:
# nenhuma camada extra de cor deve ser empilhada por cima, sob pena de escurecer
# demais a foto e comprometer a leitura dos campos.
def fundo_foto(conteudo: ft.Control, imagem: str) -> ft.Container:
    """Foto em tela cheia (`COVER`) com o conteúdo da tela por cima."""
    return ft.Container(
        content=ft.Stack(
            [
                ft.Image(
                    src=imagem,
                    fit=ft.BoxFit.COVER,
                    expand=True,
                    left=0,
                    top=0,
                    right=0,
                    bottom=0,
                ),
                conteudo,
            ],
            expand=True,
        ),
        expand=True,
        # Cor sólida por baixo da imagem: se ela não carregar, a tela continua
        # legível em vez de ficar branca.
        bgcolor=VERDE_ESCURO,
    )


def formulario_centralizado(controles: list[ft.Control]) -> ft.Column:
    """Corpo das telas sobre foto: coluna de largura fixa, centralizada e rolável.

    A largura fixa importa: sem ela, os itens alinhados à borda (o link
    "Esqueceu a senha?") acompanhariam a largura da janela em vez da do
    formulário, e se descolariam dos campos em telas largas.
    """
    return ft.Column(
        [
            ft.Container(
                content=ft.Column(
                    controles,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                width=LARGURA_FORMULARIO,
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )


def tela_de_autenticacao(
    controles: list[ft.Control],
    on_voltar=None,
    cabecalho: tuple[str, str] | None = None,
) -> ft.Container:
    """Tela completa de autenticação: foto de fundo, voltar, logo e formulário.

    É o andaime único de login, cadastro e recuperação de senha — as três telas
    passam só o próprio miolo, e por isso não têm como divergir de fundo, de
    disco do logo nem de espaçamento.

    `cabecalho` é o par (título, subtítulo) desenhado acima dos controles.
    """
    miolo: list[ft.Control] = [logo_circular(), ft.Container(height=14)]

    if cabecalho is not None:
        titulo_texto, subtitulo_texto = cabecalho
        miolo += [
            ft.Text(
                titulo_texto,
                size=20,
                weight=ft.FontWeight.BOLD,
                color=BRANCO,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                subtitulo_texto,
                size=12,
                color=MENTA_CLARA,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(height=20),
        ]

    miolo += controles

    camadas: list[ft.Control] = [formulario_centralizado(miolo)]
    if on_voltar is not None:
        # Solto no canto, fora do fluxo: não empurra o formulário do centro.
        camadas.append(
            ft.Container(
                content=ft.IconButton(
                    ICONES["voltar"], icon_color=BRANCO, icon_size=ICONE_ACAO, on_click=on_voltar
                ),
                left=-12,
                top=0,
            )
        )

    conteudo = ft.Container(
        content=ft.Stack(camadas, expand=True),
        padding=ft.Padding.symmetric(horizontal=36, vertical=16),
        expand=True,
    )
    return fundo_foto(conteudo, FOTO_DE_FUNDO)


def logo_circular(tamanho: int = LADO_DO_DISCO) -> ft.Container:
    """Logo do app dentro de um disco branco, usado no topo das quatro telas."""
    interno = int(tamanho * PROPORCAO_DO_LOGO)
    return ft.Container(
        content=ft.Image(
            src=LOGO_APP,
            width=interno,
            height=interno,
            fit=ft.BoxFit.CONTAIN,
            error_content=ft.Icon(ICONES["doacoes"], size=interno, color=VERDE_PRIMARIO),
        ),
        width=tamanho,
        height=tamanho,
        bgcolor=BRANCO,
        border_radius=tamanho / 2,
        alignment=ft.Alignment.CENTER,
    )


def rotulo_claro(texto: str) -> ft.Text:
    """Rótulo branco exibido acima de um campo, sobre a foto."""
    return ft.Text(texto, size=12, weight=ft.FontWeight.W_600, color=BRANCO)


def campo_claro(
    dica: str = "",
    senha: bool = False,
    icone: ft.IconData | None = None,
    tipo_teclado: ft.KeyboardType = ft.KeyboardType.TEXT,
    maximo: int | None = None,
    somente_numeros: bool = False,
    ao_mudar=None,
    ao_sair=None,
    ao_clicar=None,
    somente_leitura: bool = False,
    sufixo: ft.Control | None = None,
) -> ft.TextField:
    """Campo branco arredondado, sem rótulo interno (ele fica acima, em branco).

    Quando `senha=True`, o Flet já desenha o ícone de olho que mostra e oculta
    o texto digitado.

    `ao_clicar` precisa ficar **no próprio campo**, e não em um `Container` em
    volta: o `TextField` consome o clique do mouse, então um handler externo
    nunca dispara no desktop. É o que faz um campo somente-leitura abrir um
    seletor (o caso da data de nascimento).
    """
    return ft.TextField(
        hint_text=dica,
        password=senha,
        can_reveal_password=senha,
        prefix_icon=icone,
        # Todo ícone de campo no mesmo tamanho, em qualquer tela.
        prefix_icon_size_constraints=ft.BoxConstraints(
            min_width=ICONE_CAMPO, min_height=ICONE_CAMPO
        ),
        keyboard_type=tipo_teclado,
        filled=True,
        fill_color=BRANCO,
        border_radius=12,
        border_color=TRANSPARENTE,
        focused_border_color=VERDE_PRIMARIO,
        color=TEXTO_FORTE,
        cursor_color=VERDE_PRIMARIO,
        hint_style=ft.TextStyle(color=TEXTO_SECUNDARIO, size=13),
        content_padding=ft.Padding.symmetric(horizontal=16, vertical=14),
        max_length=maximo,
        # Filtrar na origem evita que a máscara receba letra e se perca.
        input_filter=ft.NumbersOnlyInputFilter() if somente_numeros else None,
        on_change=ao_mudar,
        on_blur=ao_sair,
        on_click=ao_clicar,
        read_only=somente_leitura,
        suffix=sufixo,
        error_style=ft.TextStyle(color=URGENCIA, size=11),
    )


def status_claro(texto: str, ok: bool, visivel: bool = True) -> ft.Row:
    """Linha de confirmação (verde) ou de erro (vermelho) sob um campo, sobre a foto.

    Serve ao feedback ao vivo da confirmação de senha: a cor e o ícone dizem a
    mesma coisa, de modo que a informação não depende só da cor.
    """
    cor = VERDE_CONFIRMA if ok else VERMELHO_CLARO
    return ft.Row(
        [
            ft.Icon(
                ICONES["confere"] if ok else ICONES["nao_confere"],
                size=ICONE_CAMPO - 2,
                color=cor,
            ),
            ft.Text(texto, size=11, color=cor, weight=ft.FontWeight.W_500, expand=True),
        ],
        spacing=6,
        visible=visivel,
    )


def campo_rotulado(rotulo: str, campo: ft.Control) -> ft.Column:
    """Rótulo branco acima do campo branco — o par usado em todos os formulários
    sobre foto."""
    return ft.Column(
        [rotulo_claro(rotulo), campo],
        spacing=6,
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )


def dropdown_claro(
    opcoes: list[ft.DropdownOption],
    valor: str | None = None,
    dica: str | None = None,
    desabilitado: bool = False,
    icone: ft.IconData | None = None,
    filtravel: bool = False,
    ao_selecionar=None,
) -> ft.Dropdown:
    """Seletor branco arredondado, no mesmo desenho de `campo_claro`.

    Sem rótulo interno: quem chama coloca o rótulo branco acima, via
    `campo_rotulado`.

    Com `filtravel=True` o campo vira editável e filtra a lista conforme se
    digita — é o que torna utilizável um seletor com centenas de municípios.
    """
    return ft.Dropdown(
        value=valor,
        options=opcoes,
        hint_text=dica,
        leading_icon=icone,
        disabled=desabilitado,
        editable=filtravel,
        enable_filter=filtravel,
        # No Flet 0.86 o evento de escolha do Dropdown é `on_select`.
        on_select=ao_selecionar,
        # Sem teto o menu de 645 cidades cobriria a tela inteira.
        menu_height=280,
        hint_style=ft.TextStyle(size=13, color=TEXTO_SECUNDARIO),
        # Ao contrário do TextField, o Dropdown não estica sozinho na coluna:
        # sem a largura explícita ele fica mais estreito que os campos vizinhos.
        width=LARGURA_FORMULARIO,
        filled=True,
        fill_color=BRANCO,
        border_radius=12,
        border_color=TRANSPARENTE,
        focused_border_color=VERDE_PRIMARIO,
        color=TEXTO_FORTE,
        text_style=ft.TextStyle(size=13, color=TEXTO_FORTE),
        content_padding=ft.Padding.symmetric(horizontal=16, vertical=14),
    )


def ajuda_clara(texto: str, icone: ft.IconData | None = None) -> ft.Row:
    """Linha discreta de ajuda sob um campo, legível sobre a foto."""
    return ft.Row(
        [
            ft.Icon(icone or ICONES["info"], size=ICONE_CAMPO, color=MENTA_CLARA),
            ft.Text(texto, size=11, color=MENTA_CLARA, expand=True),
        ],
        spacing=6,
    )


def link_claro(texto: str, on_click, cor: str = AMBAR_CLARO) -> ft.TextButton:
    """Link de texto legível sobre a foto (âmbar por padrão)."""
    return ft.TextButton(
        content=texto,
        on_click=on_click,
        style=ft.ButtonStyle(color=cor, padding=ft.Padding.symmetric(horizontal=8, vertical=4)),
    )


# --------------------------------------------------------------------------- #
# Superfícies e etiquetas
# --------------------------------------------------------------------------- #
def cartao(
    conteudo: ft.Control,
    padding: int = ESPACO,
    on_click=None,
    cor: str = BRANCO,
    borda: str | None = None,
) -> ft.Container:
    """Superfície branca arredondada usada em toda a interface.

    Sem borda por padrão: a separação vem de `SOMBRA_CARD`. O parâmetro `borda`
    deixou de ser o contorno cinza de todo cartão e passou a marcar exceção —
    hoje só a emergência, que recebe o contorno vermelho.
    """
    return ft.Container(
        content=conteudo,
        padding=padding,
        bgcolor=cor,
        border_radius=RAIO_CARD,
        border=ft.Border.all(1.4, borda) if borda else None,
        on_click=on_click,
        ink=on_click is not None,
        ink_color="#142E9E5B" if on_click is not None else None,
        shadow=SOMBRA_CARD,
    )


def etiqueta(
    texto: str,
    cor_texto: str = VERDE_ESCURO,
    cor_fundo: str = VERDE_SUAVE,
    icone: ft.IconData | None = None,
) -> ft.Container:
    """Pílula compacta usada em badges, chips e contadores."""
    filhos: list[ft.Control] = []
    if icone is not None:
        filhos.append(ft.Icon(icone, size=13, color=cor_texto))
    filhos.append(ft.Text(texto, size=11, weight=ft.FontWeight.W_600, color=cor_texto))

    return ft.Container(
        content=ft.Row(filhos, spacing=4, tight=True),
        padding=ft.Padding.symmetric(horizontal=10, vertical=5),
        bgcolor=cor_fundo,
        border_radius=20,
    )


def badge_urgencia(nivel: str) -> ft.Container:
    """Badge colorido de urgência — alta em vermelho, conforme o briefing."""
    cor = CORES_URGENCIA.get(nivel, TEXTO_SECUNDARIO)
    return etiqueta(
        ROTULOS_URGENCIA.get(nivel, nivel).upper(),
        cor_texto=BRANCO,
        cor_fundo=cor,
        icone=ICONES["urgente"] if nivel == "alta" else None,
    )


def badge_emergencia() -> ft.Container:
    """Selo do modo emergência, exibido acima do título do pedido."""
    return etiqueta(
        "EMERGÊNCIA", cor_texto=BRANCO, cor_fundo=URGENCIA, icone=ICONES["emergencias"]
    )


def selo_verificada() -> ft.Icon:
    """Ícone de instituição verificada."""
    return ft.Icon(ICONES["verificada"], size=16, color=VERDE_PRIMARIO, tooltip="ONG verificada")


def estrelas(nota: float, total: int | None = None, tamanho: int = 14) -> ft.Row:
    """Representação visual da avaliação: 5 estrelas + nota numérica."""
    icones: list[ft.Control] = []
    for posicao in range(1, 6):
        if nota >= posicao:
            icone = ft.Icons.STAR_ROUNDED
        elif nota >= posicao - 0.5:
            icone = ft.Icons.STAR_HALF_ROUNDED
        else:
            icone = ft.Icons.STAR_OUTLINE_ROUNDED
        icones.append(ft.Icon(icone, size=tamanho, color=AMARELO_ATENCAO))

    rotulo = f"{nota:.1f}" + (f" ({total})" if total is not None else "")
    icones.append(ft.Text(rotulo, size=12, color=TEXTO_SECUNDARIO))
    return ft.Row(icones, spacing=2, tight=True)


def icone_por_nome(nome: str, tamanho: int = ICONE_DESTAQUE, cor: str = VERDE_PRIMARIO) -> ft.Icon:
    """Converte o nome vindo da API (ex.: "water_drop") em um ícone do Flet.

    Tenta primeiro a variante contornada (`WATER_DROP_OUTLINED`) e só então a
    cheia: assim as categorias e os recursos das ONGs entram no mesmo estilo do
    resto do app sem precisar de um mapa manual — e categorias novas criadas no
    backend já nascem padronizadas. Nome desconhecido cai no ícone genérico em
    vez de quebrar a tela.
    """
    maiusculo = nome.upper()
    icone = (
        getattr(ft.Icons, f"{maiusculo}_OUTLINED", None)
        or getattr(ft.Icons, maiusculo, None)
        or ICONES["categoria_generica"]
    )
    return ft.Icon(icone, size=tamanho, color=cor)


def area_vazia(mensagem: str, icone: ft.IconData | None = None) -> ft.Container:
    """Estado vazio padronizado, exibido quando uma listagem não retorna nada."""
    return ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Icon(icone or ICONES["vazio"], size=34, color=VERDE_PRIMARIO),
                    width=78,
                    height=78,
                    bgcolor=VERDE_SUAVE,
                    border_radius=39,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Text(mensagem, size=13, color=TEXTO_SECUNDARIO, text_align=ft.TextAlign.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        ),
        padding=40,
        alignment=ft.Alignment.CENTER,
    )


def carregando(mensagem: str = "Carregando...") -> ft.Container:
    """Indicador de carregamento centralizado."""
    return ft.Container(
        content=ft.Column(
            [
                ft.ProgressRing(width=28, height=28, stroke_width=3, color=VERDE_PRIMARIO),
                ft.Text(mensagem, size=13, color=TEXTO_SECUNDARIO),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ),
        padding=40,
        alignment=ft.Alignment.CENTER,
    )
