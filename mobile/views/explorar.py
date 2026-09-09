"""Tela 5 — Explorar (busca + abas de filtro)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from mobile import theme as t
from mobile.components.comuns import cartao_oferta, cartao_solicitacao

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

    campo_busca = ft.TextField(
        value=busca,
        hint_text="Buscar por item, categoria ou bairro...",
        prefix_icon=ft.Icons.SEARCH,
        filled=True,
        fill_color=t.BRANCO,
        border_radius=14,
        border_color=t.BORDA,
        focused_border_color=t.VERDE_PRIMARIO,
        color=t.AZUL_INSTITUCIONAL,
        # `on_submit` evita uma chamada à API a cada tecla digitada.
        on_submit=lambda e: _aplicar(app, aba, e.control.value, urgencia, categoria_id),
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
                        t.subtitulo(f"{len(resultados)} resultado(s)"),
                        ft.TextButton(
                            content="Ver no mapa",
                            icon=ft.Icons.MAP_OUTLINED,
                            on_click=lambda _: app.navegar("mapa"),
                            style=ft.ButtonStyle(color=t.VERDE_PRIMARIO),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(content=_lista(app, aba, resultados), expand=False),
                ft.Container(height=18),
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


def _linha_de_abas(
    app: App, aba_ativa: str, busca: str, urgencia: str | None, categoria_id: int | None
) -> ft.Row:
    """Abas Todas / Precisando de ajuda / Oferecendo."""
    botoes: list[ft.Control] = []
    for chave, rotulo in ABAS:
        ativa = chave == aba_ativa
        botoes.append(
            ft.Container(
                content=ft.Text(
                    rotulo,
                    size=12,
                    weight=ft.FontWeight.W_600,
                    color=t.BRANCO if ativa else t.TEXTO_SECUNDARIO,
                ),
                padding=ft.Padding.symmetric(horizontal=14, vertical=9),
                bgcolor=t.VERDE_PRIMARIO if ativa else t.BRANCO,
                border_radius=20,
                border=ft.Border.all(1, t.VERDE_PRIMARIO if ativa else t.BORDA),
                on_click=lambda _, c=chave: _aplicar(app, c, busca, urgencia, categoria_id),
            )
        )
    return ft.Row(botoes, spacing=8, scroll=ft.ScrollMode.AUTO)


def _linha_de_filtros(
    app: App, aba: str, busca: str, urgencia_ativa: str | None, categoria_id: int | None
) -> ft.Row:
    """Chips de urgência e de categoria, com opção de limpar."""
    filhos: list[ft.Control] = []

    # Urgência só faz sentido para solicitações.
    if aba != "ofertas":
        for chave, rotulo in FILTROS_URGENCIA:
            ativo = chave == urgencia_ativa
            filhos.append(
                ft.Container(
                    content=ft.Text(
                        rotulo,
                        size=11,
                        color=t.BRANCO if ativo else t.TEXTO_SECUNDARIO,
                        weight=ft.FontWeight.W_600,
                    ),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=7),
                    bgcolor=(t.CORES_URGENCIA.get(chave or "", t.AZUL_INSTITUCIONAL)
                             if ativo else t.BRANCO),
                    border_radius=18,
                    border=ft.Border.all(1, t.BORDA),
                    on_click=lambda _, c=chave: _aplicar(app, aba, busca, c, categoria_id),
                )
            )

    if categoria_id is not None:
        nome = next(
            (c["nome"] for c in app.categorias() if c["id"] == categoria_id), "Categoria"
        )
        filhos.append(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Text(nome, size=11, color=t.BRANCO, weight=ft.FontWeight.W_600),
                        ft.Icon(ft.Icons.CLOSE, size=13, color=t.BRANCO),
                    ],
                    spacing=4,
                    tight=True,
                ),
                padding=ft.Padding.symmetric(horizontal=12, vertical=7),
                bgcolor=t.AZUL_INSTITUCIONAL,
                border_radius=18,
                on_click=lambda _: _aplicar(app, aba, busca, urgencia_ativa, None),
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
            "Nada encontrado com esses filtros.\nTente outra busca ou limpe os filtros.",
            ft.Icons.SEARCH_OFF,
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

    return ft.Column(cartoes, spacing=10)
