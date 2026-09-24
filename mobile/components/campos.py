"""
Campos de formulário do app — um desenho só, para todas as telas.

Antes deste módulo havia duas famílias de campo convivendo: `theme.campo()`,
com rótulo flutuante dentro da moldura, e `theme.campo_claro()`, com rótulo
fora. Elas não diferiam só no rótulo — mudavam de altura, de largura e de raio,
e o resultado aparecia lado a lado na mesma tela.

Três defeitos concretos que este módulo resolve:

* **Altura instável.** Com `label=` dentro, o campo tem uma altura quando está
  vazio (o rótulo ocupa o lugar do texto) e outra quando tem valor (o rótulo
  encolhe e sobe). Em *Nova solicitação*, "Quantidade" e "Quantas pessoas"
  ficavam com alturas diferentes só porque uma delas vinha preenchida. Aqui a
  altura é fixa (`t.ALTURA_CAMPO`) e o rótulo vive fora do campo.
* **Largura menor que a coluna.** Um `TextField` dentro de uma `Column`
  alinhada em `START` recebe restrição frouxa e assume a largura natural —
  por isso os campos terminavam antes do botão. `com_rotulo` e `formulario`
  usam `STRETCH`, e aí todo campo ocupa a coluna inteira.
* **Seletor fora de linha.** O `Dropdown`, ao contrário do `TextField`, não
  estica sozinho: ficava com uma largura fixa que não acompanhava o resto.
  `com_rotulo` embrulha todo seletor em uma `Row` com `expand`, e ele passa a
  medir exatamente o mesmo que os campos de texto.

O rótulo é sempre **acima** do campo. A única variação permitida é a cor: nas
telas sobre foto (login, cadastro, recuperar senha) ele é branco, porque
`TEXTO_FORTE` sobre a fotografia não se lê. É o `sobre_foto=True`.
"""

from __future__ import annotations

from typing import Any, Callable

import flet as ft

from mobile import theme as t

# Cor dos ícones dentro do campo: o cinza-esverdeado de apoio da paleta. O
# ícone situa o campo, não compete com o que a pessoa digitou.
COR_DO_ICONE = t.TEXTO_SECUNDARIO


def _icone(icone: ft.IconData | None, cor: str = COR_DO_ICONE) -> ft.Icon | None:
    """Ícone do campo no tamanho e na cor únicos.

    Vai como `Control` (e não como `IconData`) porque só assim dá para fixar a
    cor: passando o enum, o campo pinta o ícone com a cor do tema, que muda
    conforme o estado de foco.
    """
    if icone is None:
        return None
    return ft.Icon(icone, size=t.ICONE_CAMPO, color=cor)


def campo_texto(
    dica: str = "",
    valor: str = "",
    senha: bool = False,
    icone: ft.IconData | None = None,
    tipo_teclado: ft.KeyboardType = ft.KeyboardType.TEXT,
    maximo: int | None = None,
    somente_numeros: bool = False,
    ao_mudar: Callable[..., Any] | None = None,
    ao_sair: Callable[..., Any] | None = None,
    ao_clicar: Callable[..., Any] | None = None,
    ao_enviar: Callable[..., Any] | None = None,
    somente_leitura: bool = False,
    sufixo: ft.Control | None = None,
) -> ft.TextField:
    """Campo de texto de uma linha — o padrão de entrada do app.

    Com `senha=True` o Flet já desenha o olho que mostra e oculta o texto.

    `ao_clicar` precisa ficar **no próprio campo**, e não em um `Container` em
    volta: o `TextField` consome o clique do mouse, então um handler externo
    nunca dispara no desktop. É o que faz um campo somente-leitura abrir um
    seletor (o caso da data de nascimento, no cadastro).
    """
    return ft.TextField(
        value=valor,
        hint_text=dica,
        password=senha,
        can_reveal_password=senha,
        prefix_icon=_icone(icone),
        keyboard_type=tipo_teclado,
        height=t.ALTURA_CAMPO,
        filled=True,
        fill_color=t.BRANCO,
        border_radius=t.RAIO_CAMPO,
        border_color=t.TRANSPARENTE,
        focused_border_color=t.VERDE_PRIMARIO,
        color=t.TEXTO_FORTE,
        cursor_color=t.VERDE_PRIMARIO,
        text_style=ft.TextStyle(size=13.5, color=t.TEXTO_FORTE),
        hint_style=ft.TextStyle(color=t.TEXTO_SECUNDARIO, size=13),
        content_padding=ft.Padding.symmetric(horizontal=16, vertical=0),
        max_length=maximo,
        # O contador ("15/15") é do Flet, e só aparece em campo com limite. Fica
        # discreto: 10px no cinza inativo, para informar sem disputar com o
        # rótulo do campo seguinte.
        counter_style=ft.TextStyle(size=10, color=t.TEXTO_INATIVO),
        # Filtrar na origem evita que a máscara receba letra e se perca.
        input_filter=ft.NumbersOnlyInputFilter() if somente_numeros else None,
        on_change=ao_mudar,
        on_blur=ao_sair,
        on_click=ao_clicar,
        on_submit=ao_enviar,
        read_only=somente_leitura,
        suffix=sufixo,
        error_style=ft.TextStyle(color=t.URGENCIA, size=11),
    )


def campo_area_texto(
    dica: str = "",
    valor: str = "",
    linhas: int = t.LINHAS_AREA_TEXTO,
    maximo: int | None = None,
    ao_mudar: Callable[..., Any] | None = None,
) -> ft.TextField:
    """Área de texto (multiline) — mesmo fundo, raio e largura; só mais alta.

    A altura vem do número de linhas, e não de `t.ALTURA_CAMPO`: fixar a altura
    aqui brigaria com o crescimento do texto. O que se mantém idêntico é tudo o
    que se enxerga na borda — branco, raio 14, largura da coluna.
    """
    return ft.TextField(
        value=valor,
        hint_text=dica,
        multiline=True,
        min_lines=linhas,
        max_lines=linhas + 2,
        filled=True,
        fill_color=t.BRANCO,
        border_radius=t.RAIO_CAMPO,
        border_color=t.TRANSPARENTE,
        focused_border_color=t.VERDE_PRIMARIO,
        color=t.TEXTO_FORTE,
        cursor_color=t.VERDE_PRIMARIO,
        text_style=ft.TextStyle(size=13.5, color=t.TEXTO_FORTE),
        hint_style=ft.TextStyle(color=t.TEXTO_SECUNDARIO, size=13),
        content_padding=ft.Padding.symmetric(horizontal=16, vertical=14),
        max_length=maximo,
        counter_style=ft.TextStyle(size=10, color=t.TEXTO_INATIVO),
        on_change=ao_mudar,
        error_style=ft.TextStyle(color=t.URGENCIA, size=11),
    )


def campo_dropdown(
    opcoes: list[ft.DropdownOption],
    valor: str | None = None,
    dica: str | None = None,
    desabilitado: bool = False,
    icone: ft.IconData | None = None,
    filtravel: bool = False,
    ao_selecionar: Callable[..., Any] | None = None,
) -> ft.Dropdown:
    """Seletor com o mesmo desenho do campo de texto.

    Com `filtravel=True` ele vira editável e filtra a lista conforme se digita —
    é o que torna utilizável um seletor com centenas de municípios.

    Sem `width`: quem dá a largura é o `com_rotulo`, que o embrulha em uma `Row`
    com `expand`. Uma largura fixa aqui voltaria a desalinhar o seletor dos
    campos vizinhos assim que a coluna mudasse de tamanho.
    """
    return ft.Dropdown(
        value=valor,
        options=opcoes,
        hint_text=dica,
        leading_icon=_icone(icone),
        disabled=desabilitado,
        editable=filtravel,
        enable_filter=filtravel,
        # No Flet 0.86 o evento de escolha do Dropdown é `on_select`.
        on_select=ao_selecionar,
        # Sem teto o menu de 645 cidades cobriria a tela inteira.
        menu_height=280,
        expand=True,
        height=t.ALTURA_CAMPO,
        filled=True,
        fill_color=t.BRANCO,
        border_radius=t.RAIO_CAMPO,
        border_color=t.TRANSPARENTE,
        focused_border_color=t.VERDE_PRIMARIO,
        color=t.TEXTO_FORTE,
        text_style=ft.TextStyle(size=13.5, color=t.TEXTO_FORTE),
        hint_style=ft.TextStyle(size=13, color=t.TEXTO_SECUNDARIO),
        content_padding=ft.Padding.symmetric(horizontal=16, vertical=0),
    )


def campo_travado(
    valor: str,
    icone: ft.IconData | None = None,
    explicacao: str | None = None,
) -> ft.Control:
    """Dado que a tela mostra mas não deixa editar, com cadeado à direita.

    Mesma altura e mesmo raio dos campos editáveis — o que muda é o fundo
    acinzentado e o cadeado, que juntos dizem "isto aqui não se digita" sem
    precisar de aviso. Hoje só o CPF usa este campo.
    """
    caixa = ft.Container(
        content=ft.Row(
            [
                *( [_icone(icone)] if icone else [] ),
                ft.Text(valor or "—", size=13.5, color=t.TEXTO_SECUNDARIO, expand=True),
                ft.Icon(ft.Icons.LOCK_OUTLINE_ROUNDED, size=15, color=t.TEXTO_INATIVO),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=16),
        height=t.ALTURA_CAMPO,
        bgcolor=t.CINZA_CLARO,
        border_radius=t.RAIO_CAMPO,
    )
    if not explicacao:
        return caixa
    return ft.Column(
        [caixa, ft.Text(explicacao, size=10.5, color=t.TEXTO_SECUNDARIO)],
        spacing=5,
    )


def com_rotulo(
    rotulo: str,
    campo: ft.Control,
    apoio: str | None = None,
    sobre_foto: bool = False,
) -> ft.Column:
    """Rótulo acima do campo — o único padrão de rótulo do app.

    `sobre_foto` troca a cor do rótulo para branco nas telas com fotografia de
    fundo (login, cadastro, recuperar senha), onde o `TEXTO_FORTE` sumiria.

    O `Dropdown` entra embrulhado em uma `Row`: ele não estica sozinho dentro de
    uma `Column`, e é `expand` em eixo horizontal que o faz medir o mesmo que os
    campos de texto.
    """
    if isinstance(campo, ft.Dropdown):
        campo = ft.Row([campo], spacing=0)

    filhos: list[ft.Control] = [
        ft.Text(
            rotulo,
            size=12,
            weight=ft.FontWeight.W_600,
            color=t.BRANCO if sobre_foto else t.TEXTO_FORTE,
        ),
        campo,
    ]
    if apoio:
        filhos.append(
            ft.Text(
                apoio,
                size=10.5,
                color=t.MENTA_CLARA if sobre_foto else t.TEXTO_SECUNDARIO,
            )
        )

    return ft.Column(
        filhos,
        spacing=6,
        # STRETCH, e não START: com restrição frouxa o campo assume a largura
        # natural e termina antes da coluna.
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )


def formulario(controles: list[ft.Control], **kwargs: Any) -> ft.Column:
    """Coluna de campos com o respiro vertical único (`t.ESPACO_CAMPOS`).

    Também em `STRETCH`, para que um campo solto (sem `com_rotulo`) colocado
    aqui dentro ocupe a coluna inteira, como todos os outros.
    """
    kwargs.setdefault("spacing", t.ESPACO_CAMPOS)
    kwargs.setdefault("horizontal_alignment", ft.CrossAxisAlignment.STRETCH)
    return ft.Column(controles, **kwargs)
