"""Tela de leitura dos documentos legais (Termos de Uso e Política de Privacidade).

Uma tela só serve aos dois documentos: o parâmetro `documento` da rota diz qual
carregar (`"termos"` ou `"privacidade"`). O conteúdo vem de `mobile.legal_textos`,
que lê os arquivos `.md` de `assets/legal`.

Sai do padrão das telas sobre foto de propósito: documento é para ler, e texto
corrido pede fundo claro, largura controlada e rolagem — não a foto de fundo das
telas de autenticação.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from mobile import legal_textos
from mobile import theme as t
from mobile.components.comuns import cabecalho

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App


def _folha_de_estilo() -> ft.MarkdownStyleSheet:
    """Tipografia do documento, no padrão visual do app.

    Sem isso o `ft.Markdown` cai no tema do Flutter: títulos pretos e corpo em
    tamanho de página web, que ficam grandes demais em 430 px de largura.
    """
    return ft.MarkdownStyleSheet(
        p_text_style=ft.TextStyle(size=13, color=t.TEXTO_FORTE, height=1.5),
        h1_text_style=ft.TextStyle(
            size=19, weight=ft.FontWeight.BOLD, color=t.TEXTO_FORTE
        ),
        h2_text_style=ft.TextStyle(
            size=15, weight=ft.FontWeight.BOLD, color=t.VERDE_ESCURO
        ),
        h3_text_style=ft.TextStyle(
            size=14, weight=ft.FontWeight.W_600, color=t.TEXTO_FORTE
        ),
        strong_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=t.TEXTO_FORTE),
        em_text_style=ft.TextStyle(italic=True, color=t.TEXTO_SECUNDARIO),
        a_text_style=ft.TextStyle(color=t.VERDE_PRIMARIO, weight=ft.FontWeight.W_600),
        blockquote_text_style=ft.TextStyle(size=12, color=t.TEXTO_SECUNDARIO, height=1.45),
        blockquote_decoration=ft.BoxDecoration(
            bgcolor=t.VERDE_SUAVE,
            border_radius=ft.BorderRadius.all(10),
        ),
        blockquote_padding=ft.Padding.all(12),
        table_head_text_style=ft.TextStyle(
            size=12, weight=ft.FontWeight.BOLD, color=t.TEXTO_FORTE
        ),
        table_body_text_style=ft.TextStyle(size=12, color=t.TEXTO_FORTE),
        table_cells_padding=ft.Padding.symmetric(horizontal=8, vertical=6),
        list_bullet_text_style=ft.TextStyle(size=13, color=t.TEXTO_FORTE),
        block_spacing=10,
    )


def construir(app: App) -> ft.Control:
    """Documento legal escolhido pela rota, rolável e com botão de voltar."""
    chave = app.state.rota_atual.parametros.get("documento", legal_textos.PADRAO)

    corpo = ft.Container(
        content=ft.Column(
            [
                ft.Markdown(
                    legal_textos.texto(chave),
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                    md_style_sheet=_folha_de_estilo(),
                ),
                # Respiro no fim: sem ele a última linha encosta na borda.
                ft.Container(height=24),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=12),
        expand=True,
    )

    return ft.Column(
        [
            cabecalho(
                legal_textos.titulo(chave),
                ao_voltar=app.voltar,
                subtitulo="Projeto acadêmico Conecta Comunidade",
            ),
            corpo,
        ],
        spacing=0,
        expand=True,
    )
