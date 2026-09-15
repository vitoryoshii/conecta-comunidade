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
AZUL_INSTITUCIONAL = "#0E2A47"  # títulos e textos de destaque
FUNDO_CLARO = "#F5F7F6"         # fundo das telas
URGENCIA = "#E23B3B"            # alertas, urgência alta, modo emergência
TEXTO_SECUNDARIO = "#6B7B72"    # legendas, metadados, textos de apoio

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

# Cores dos pins do mapa, por tipo de ponto.
CORES_MAPA = {
    "ajuda": URGENCIA,
    "oferecendo": VERDE_PRIMARIO,
    "ong": AZUL_INSTITUCIONAL,
    "ponto_retirada": AMARELO_ATENCAO,
}

ICONES_MAPA = {
    "ajuda": ft.Icons.VOLUNTEER_ACTIVISM,
    "oferecendo": ft.Icons.CARD_GIFTCARD,
    "ong": ft.Icons.APARTMENT,
    "ponto_retirada": ft.Icons.STOREFRONT,
}

ROTULOS_MAPA = {
    "ajuda": "Precisa de ajuda",
    "oferecendo": "Oferecendo",
    "ong": "ONGs",
    "ponto_retirada": "Pontos de retirada",
}

# Arquivos da marca servidos pelo `assets_dir` do Flet.
LOGO_SIMBOLO = "brand/logo/logo-symbol.svg"

# Raio padrão de arredondamento e espaçamento base das telas.
RAIO = 16
ESPACO = 16

# Largura útil do formulário nas telas sobre foto: a janela de demonstração
# tem 430px e a tela reserva 36px de padding de cada lado.
LARGURA_FORMULARIO = 358

# Cores auxiliares para categorias, usadas em ícones e fundos suaves.
CORES_CATEGORIAS = [
    (VERDE_PRIMARIO, VERDE_SUAVE),
    ("#0E2A47", "#E7EEF4"),
    ("#E23B3B", "#FCEAEA"),
    (AMARELO_ATENCAO, "#FFF4DC"),
    (TEAL, "#E4FBF8"),
    (MENTA, "#EDFBF2"),
    ("#7C3AED", "#F1EAFF"),
]


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
def titulo(texto: str, tamanho: int = 22, cor: str = AZUL_INSTITUCIONAL) -> ft.Text:
    """Título de tela ou de seção."""
    return ft.Text(texto, size=tamanho, weight=ft.FontWeight.BOLD, color=cor)


def subtitulo(texto: str, tamanho: int = 13, cor: str = TEXTO_SECUNDARIO) -> ft.Text:
    """Texto de apoio, usado em legendas e metadados."""
    return ft.Text(texto, size=tamanho, color=cor)


def corpo(texto: str, tamanho: int = 14, cor: str = AZUL_INSTITUCIONAL, **kwargs) -> ft.Text:
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
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=14)),
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
            shape=ft.RoundedRectangleBorder(radius=14),
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
        keyboard_type=tipo_teclado,
        filled=True,
        fill_color=BRANCO,
        border_radius=12,
        border_color=BORDA,
        focused_border_color=VERDE_PRIMARIO,
        color=AZUL_INSTITUCIONAL,
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


def logo_circular(tamanho: int = 60) -> ft.Container:
    """Símbolo da marca dentro de um disco branco, usado no topo das telas."""
    interno = int(tamanho * 0.62)
    return ft.Container(
        content=ft.Image(
            src=LOGO_SIMBOLO,
            width=interno,
            height=interno,
            fit=ft.BoxFit.CONTAIN,
            error_content=ft.Icon(ft.Icons.FAVORITE, size=interno, color=VERDE_PRIMARIO),
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
) -> ft.TextField:
    """Campo branco arredondado, sem rótulo interno (ele fica acima, em branco).

    Quando `senha=True`, o Flet já desenha o ícone de olho que mostra e oculta
    o texto digitado.
    """
    return ft.TextField(
        hint_text=dica,
        password=senha,
        can_reveal_password=senha,
        prefix_icon=icone,
        keyboard_type=tipo_teclado,
        filled=True,
        fill_color=BRANCO,
        border_radius=12,
        border_color=TRANSPARENTE,
        focused_border_color=VERDE_PRIMARIO,
        color=AZUL_INSTITUCIONAL,
        cursor_color=VERDE_PRIMARIO,
        hint_style=ft.TextStyle(color=TEXTO_SECUNDARIO, size=13),
        content_padding=ft.Padding.symmetric(horizontal=16, vertical=14),
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
    """Superfície branca arredondada usada em toda a interface."""
    return ft.Container(
        content=conteudo,
        padding=padding,
        bgcolor=cor,
        border_radius=RAIO,
        border=ft.Border.all(1, borda or BORDA),
        on_click=on_click,
        ink=on_click is not None,
        ink_color="#142E9E5B" if on_click is not None else None,
        shadow=ft.BoxShadow(blur_radius=10, color="#120E2A47", offset=ft.Offset(0, 3)),
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
        icone=ft.Icons.PRIORITY_HIGH if nivel == "alta" else None,
    )


def badge_emergencia() -> ft.Container:
    """Selo do modo emergência, exibido acima do título do pedido."""
    return etiqueta(
        "EMERGÊNCIA", cor_texto=BRANCO, cor_fundo=URGENCIA, icone=ft.Icons.CRISIS_ALERT
    )


def selo_verificada() -> ft.Icon:
    """Ícone de instituição verificada."""
    return ft.Icon(ft.Icons.VERIFIED, size=16, color=VERDE_PRIMARIO, tooltip="ONG verificada")


def estrelas(nota: float, total: int | None = None, tamanho: int = 14) -> ft.Row:
    """Representação visual da avaliação: 5 estrelas + nota numérica."""
    icones: list[ft.Control] = []
    for posicao in range(1, 6):
        if nota >= posicao:
            icone = ft.Icons.STAR
        elif nota >= posicao - 0.5:
            icone = ft.Icons.STAR_HALF
        else:
            icone = ft.Icons.STAR_BORDER
        icones.append(ft.Icon(icone, size=tamanho, color=AMARELO_ATENCAO))

    rotulo = f"{nota:.1f}" + (f" ({total})" if total is not None else "")
    icones.append(ft.Text(rotulo, size=12, color=TEXTO_SECUNDARIO))
    return ft.Row(icones, spacing=2, tight=True)


def icone_por_nome(nome: str, tamanho: int = 22, cor: str = VERDE_PRIMARIO) -> ft.Icon:
    """Converte o nome vindo da API (ex.: "water_drop") em um ícone do Flet.

    Se o nome não existir na enumeração, cai para um ícone genérico em vez de
    quebrar a tela.
    """
    icone = getattr(ft.Icons, nome.upper(), ft.Icons.CATEGORY)
    return ft.Icon(icone, size=tamanho, color=cor)


def area_vazia(mensagem: str, icone: ft.IconData = ft.Icons.INBOX) -> ft.Container:
    """Estado vazio padronizado, exibido quando uma listagem não retorna nada."""
    return ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Icon(icone, size=34, color=VERDE_PRIMARIO),
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
