"""Formulário de nova oferta (fluxo "Quero ajudar / Doar")."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from mobile import theme as t
from mobile.components import campos
from mobile.components.comuns import cabecalho
from mobile.views.quero_ajudar import OPCOES, _cartao_opcao

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App


def construir(app: App) -> ft.Control:
    """Monta o formulário de publicação de uma oferta avulsa."""
    categorias = app.categorias()

    campo_titulo = campos.campo_texto(
        "Ex.: água mineral e cestas básicas", icone=t.ICONES["titulo"]
    )
    campo_descricao = campos.campo_area_texto(
        "Ex.: 30 litros de água mineral, retirada das 8h às 20h."
    )
    campo_endereco = campos.campo_texto("Rua, bairro ou região", icone=t.ICONES["local"])

    seletor_categoria = campos.campo_dropdown(
        [ft.DropdownOption(key=str(c["id"]), text=c["nome"]) for c in categorias],
        valor=str(categorias[0]["id"]) if categorias else None,
        icone=t.ICONES["categoria"],
    )

    escolhido = ["tenho_item"]
    opcoes_coluna = ft.Column(spacing=10)

    def desenhar_opcoes() -> None:
        """Redesenha os cartões de tipo de ajuda marcando o selecionado."""
        opcoes_coluna.controls = [
            _cartao_opcao(chave, titulo, descricao, icone, escolhido[0] == chave, selecionar)
            for chave, titulo, descricao, icone in OPCOES
        ]

    def selecionar(chave: str) -> None:
        """Guarda o tipo escolhido e atualiza a tela."""
        escolhido[0] = chave
        desenhar_opcoes()
        app.page.update()

    desenhar_opcoes()

    def publicar(_: ft.ControlEvent) -> None:
        """Valida e envia a oferta para a API."""
        titulo = (campo_titulo.value or "").strip()
        if len(titulo) < 3:
            app.aviso("Descreva o que você está oferecendo.", erro=True)
            return
        if not seletor_categoria.value:
            app.aviso("Escolha uma categoria.", erro=True)
            return

        criada = app.executar(
            lambda: app.api.criar_oferta(
                {
                    "titulo": titulo,
                    "descricao": campo_descricao.value or "",
                    "categoria_id": int(seletor_categoria.value),
                    "tipo_ajuda": escolhido[0],
                    "endereco": campo_endereco.value or "",
                }
            ),
            "Oferta publicada! Quem precisa já pode encontrá-la.",
        )
        if criada is None:
            return

        app.substituir("explorar", aba="ofertas")

    return ft.Column(
        [
            cabecalho("Quero ajudar / Doar", app.voltar),
            ft.Container(
                content=campos.formulario(
                    [
                        t.subtitulo("Sua oferta aparece na busca e no mapa da comunidade."),
                        campos.com_rotulo("O que você está oferecendo?", campo_titulo),
                        campos.com_rotulo("Categoria", seletor_categoria),
                        campos.com_rotulo("Detalhes", campo_descricao),
                        campos.com_rotulo("Endereço ou região", campo_endereco),
                        ft.Text(
                            "Como você pode ajudar?",
                            size=12,
                            weight=ft.FontWeight.W_600,
                            color=t.TEXTO_FORTE,
                        ),
                        opcoes_coluna,
                        ft.Container(height=4),
                        t.botao_primario("Publicar oferta", publicar, t.ICONES["enviar"], 400),
                        ft.Container(height=16),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
                padding=ft.Padding.symmetric(horizontal=20, vertical=16),
                expand=True,
                bgcolor=t.FUNDO_CLARO,
            ),
        ],
        spacing=0,
        expand=True,
    )
