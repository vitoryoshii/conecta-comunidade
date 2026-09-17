"""Tela 5 — Explorar (busca + abas de filtro)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from mobile import theme as t
from mobile.components.comuns import cartao_oferta, cartao_solicitacao
from mobile.components.fab import ESPACO_PARA_O_FAB

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

# Abas da tela. A aba define qual endpoint é consultado.
ABAS = [
    ("todas", "Todas"),
    ("ajuda", "Precisando de ajuda"),
    ("ofertas", "Oferecendo"),
]

FILTROS_URGENCIA = [
    (None, "Qualquer urgência"),
    ("alta", "Urgente"),
    ("media", "Média"),
    ("baixa", "Baixa"),
]


def construir(app: App) -> ft.Control:
    """Monta a busca, as abas e a lista de resultados."""
    parametros = app.state.rota_atual.parametros
    aba: str = parametros.get("aba", "todas")
    busca: str = parametros.get("busca", "")
    urgencia: str | None = parametros.get("urgencia")
    categoria_id: int | None = parametros.get("categoria_id")

    # A barra de busca é uma superfície branca com sombra, como os cartões: sem
    # contorno, ela pertence à mesma família visual do resto da tela.
    campo_busca = ft.Container(
        content=ft.TextField(
            value=busca,
            hint_text="Buscar por item, categoria ou bairro...",
            prefix_icon=t.ICONES["buscar"],
            filled=True,
            fill_color=t.BRANCO,
            border_radius=t.RAIO_BOTAO,
            border_color=t.TRANSPARENTE,
            focused_border_color=t.TRANSPARENTE,
            color=t.TEXTO_FORTE,
            hint_style=ft.TextStyle(size=13, color=t.TEXTO_SECUNDARIO),
            content_padding=ft.Padding.symmetric(horizontal=14, vertical=13),
            # `on_submit` evita uma chamada à API a cada tecla digitada.
            on_submit=lambda e: _aplicar(app, aba, e.control.value, urgencia, categoria_id),
        ),
        border_radius=t.RAIO_BOTAO,
        shadow=t.SOMBRA_CARD,
    )

    resultados = _buscar(app, aba, busca, urgencia, categoria_id)

    return ft.Container(
        content=ft.Column(
            [
                t.titulo("Explorar", 22),
                campo_busca,
                _linha_de_abas(app, aba, busca, urgencia, categoria_id),
                _linha_de_filtros(app, aba, busca, urgencia, categoria_id),
                ft.Row(
                    [
                        ft.Text(
                            f"{len(resultados)} resultado{'s' if len(resultados) != 1 else ''}",
                            size=12.5,
                            weight=ft.FontWeight.W_600,
                            color=t.TEXTO_SECUNDARIO,
                        ),
                        _atalho_do_mapa(app),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(content=_lista(app, aba, resultados), expand=False),
                # Folga para o último cartão não terminar embaixo do FAB.
                ft.Container(height=ESPACO_PARA_O_FAB),
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=16),
        expand=True,
        bgcolor=t.FUNDO_CLARO,
    )


def _aplicar(
    app: App, aba: str, busca: str, urgencia: str | None, categoria_id: int | None
) -> None:
    """Reabre a tela com os novos filtros (sem crescer a pilha)."""
    app.substituir(
        "explorar", aba=aba, busca=busca or "", urgencia=urgencia, categoria_id=categoria_id
    )


def _pilula(
    rotulo: str,
    ativa: bool,
    on_click,
    cor_ativa: str = t.VERDE_PRIMARIO,
    icone: ft.IconData | None = None,
) -> ft.Container:
    """Chip de filtro: sólido quando ativo, branco com sombra quando não.

    O contorno cinza saiu: inativa, a pílula se separa do fundo pela sombra —
    o mesmo recurso dos cartões, o que mantém a tela com uma linguagem só.
    """
    filhos: list[ft.Control] = []
    if icone is not None:
        filhos.append(ft.Icon(icone, size=14, color=t.BRANCO if ativa else t.TEXTO_SECUNDARIO))
    filhos.append(
        ft.Text(
            rotulo,
            size=12,
            weight=ft.FontWeight.W_600,
            color=t.BRANCO if ativa else t.TEXTO_SECUNDARIO,
        )
    )

    return ft.Container(
        content=ft.Row(filhos, spacing=5, tight=True),
        padding=ft.Padding.symmetric(horizontal=14, vertical=9),
        bgcolor=cor_ativa if ativa else t.BRANCO,
        border_radius=20,
        shadow=t.SOMBRA_CARD,
        on_click=on_click,
        ink=True,
    )


def _atalho_do_mapa(app: App) -> ft.Container:
    """Link "Ver no mapa" ao lado do contador de resultados."""
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(t.ICONES["estado"], size=16, color=t.VERDE_PRIMARIO),
                ft.Text(
                    "Ver no mapa", size=12, weight=ft.FontWeight.W_600, color=t.VERDE_PRIMARIO
                ),
            ],
            spacing=5,
            tight=True,
        ),
        on_click=lambda _: app.navegar("mapa"),
        padding=ft.Padding.symmetric(horizontal=6, vertical=4),
        border_radius=10,
        ink=True,
    )


def _linha_de_abas(
    app: App, aba_ativa: str, busca: str, urgencia: str | None, categoria_id: int | None
) -> ft.Row:
    """Abas Todas / Precisando de ajuda / Oferecendo."""
    botoes = [
        _pilula(
            rotulo,
            chave == aba_ativa,
            lambda _, c=chave: _aplicar(app, c, busca, urgencia, categoria_id),
        )
        for chave, rotulo in ABAS
    ]
    return ft.Row(botoes, spacing=8, scroll=ft.ScrollMode.AUTO)


def _linha_de_filtros(
    app: App, aba: str, busca: str, urgencia_ativa: str | None, categoria_id: int | None
) -> ft.Row:
    """Chips de urgência e de categoria, com opção de limpar."""
    filhos: list[ft.Control] = []

    # Urgência só faz sentido para solicitações.
    if aba != "ofertas":
        for chave, rotulo in FILTROS_URGENCIA:
            filhos.append(
                _pilula(
                    rotulo,
                    chave == urgencia_ativa,
                    lambda _, c=chave: _aplicar(app, aba, busca, c, categoria_id),
                    cor_ativa=t.CORES_URGENCIA.get(chave or "", t.TEXTO_FORTE),
                )
            )

    if categoria_id is not None:
        nome = next(
            (c["nome"] for c in app.categorias() if c["id"] == categoria_id), "Categoria"
        )
        # A pílula da categoria carrega a cor da própria categoria e um "x":
        # ela é o único filtro que se remove tocando nele mesmo.
        cor_icone, _ = t.cores_da_categoria(
            next((c.get("icone") for c in app.categorias() if c["id"] == categoria_id), None)
        )
        filhos.append(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Text(nome, size=12, color=t.BRANCO, weight=ft.FontWeight.W_600),
                        ft.Icon(t.ICONES["fechar"], size=14, color=t.BRANCO),
                    ],
                    spacing=5,
                    tight=True,
                ),
                padding=ft.Padding.symmetric(horizontal=14, vertical=9),
                bgcolor=cor_icone,
                border_radius=20,
                shadow=t.SOMBRA_CARD,
                on_click=lambda _: _aplicar(app, aba, busca, urgencia_ativa, None),
                ink=True,
                tooltip="Remover o filtro de categoria",
            )
        )

    return ft.Row(filhos, spacing=8, scroll=ft.ScrollMode.AUTO)


def _buscar(
    app: App, aba: str, busca: str, urgencia: str | None, categoria_id: int | None
) -> list[dict[str, Any]]:
    """Consulta a API conforme a aba selecionada.

    Na aba "Todas" juntamos solicitações e ofertas em uma lista só, marcando
    cada item com a chave `_tipo` para o cartão certo ser escolhido depois.
    """
    coords = app.coordenadas()
    itens: list[dict[str, Any]] = []

    if aba in {"todas", "ajuda"}:
        solicitacoes = app.executar(
            lambda: app.api.listar_solicitacoes(
                busca=busca or None,
                urgencia=urgencia,
                categoria_id=categoria_id,
                ordenar_por="distancia",
                **coords,
            )
        ) or []
        itens += [{**item, "_tipo": "solicitacao"} for item in solicitacoes]

    if aba in {"todas", "ofertas"}:
        ofertas = app.executar(
            lambda: app.api.listar_ofertas(
                busca=busca or None,
                categoria_id=categoria_id,
                status="disponivel",
                ordenar_por="distancia",
                **coords,
            )
        ) or []
        itens += [{**item, "_tipo": "oferta"} for item in ofertas]

    if aba == "todas":
        # Emergências primeiro; depois, do mais próximo ao mais distante.
        itens.sort(
            key=lambda i: (
                not i.get("emergencia", False),
                i.get("distancia_km") if i.get("distancia_km") is not None else float("inf"),
            )
        )

    return itens


def _lista(app: App, aba: str, itens: list[dict[str, Any]]) -> ft.Control:
    """Renderiza o cartão adequado a cada item da lista."""
    if not itens:
        return t.area_vazia(
            "Nada por aqui com esses filtros.\nTente outra busca, ou toque em Todas para ver o que está aberto.",
            t.ICONES["sem_resultado"],
        )

    cartoes: list[ft.Control] = []
    for item in itens:
        tipo = item.get("_tipo", "solicitacao" if aba != "ofertas" else "oferta")
        if tipo == "solicitacao":
            cartoes.append(
                cartao_solicitacao(item, lambda i: app.navegar("detalhe_solicitacao", id=i))
            )
        else:
            cartoes.append(cartao_oferta(item))

    return ft.Column(cartoes, spacing=12)
