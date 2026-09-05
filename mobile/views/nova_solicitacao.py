"""Formulário de nova solicitação (fluxo "Preciso de ajuda")."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from mobile import theme as t
from mobile.components.comuns import cabecalho

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

NIVEIS_URGENCIA = [("baixa", "Baixa"), ("media", "Média"), ("alta", "Urgente")]


def construir(app: App) -> ft.Control:
    """Monta o formulário de publicação de um pedido de ajuda."""
    categorias = app.categorias()

    campo_titulo = t.campo("O que você precisa?", icone=ft.Icons.TITLE)
    campo_descricao = t.campo(
        "Conte um pouco mais",
        multilinha=True,
        dica="Explique a situação para quem for ajudar.",
    )
    campo_quantidade = t.campo("Quantidade", dica="Ex.: 50 litros, 7 cestas", icone=ft.Icons.NUMBERS)
    campo_pessoas = t.campo(
        "Quantas pessoas serão beneficiadas?",
        valor="1",
        icone=ft.Icons.GROUP_OUTLINED,
        tipo_teclado=ft.KeyboardType.NUMBER,
    )
    campo_endereco = t.campo("Endereço ou ponto de referência", icone=ft.Icons.PLACE_OUTLINED)

    seletor_categoria = ft.Dropdown(
        label="Categoria",
        value=str(categorias[0]["id"]) if categorias else None,
        options=[
            ft.DropdownOption(key=str(c["id"]), text=c["nome"]) for c in categorias
        ],
        filled=True,
        fill_color=t.BRANCO,
        border_radius=12,
        border_color=t.BORDA,
        color=t.AZUL_INSTITUCIONAL,
    )

    urgencia = ["media"]
    linha_urgencia = ft.Row(spacing=8)

    def desenhar_urgencia() -> None:
        """Redesenha os botões de urgência marcando o nível selecionado."""
        linha_urgencia.controls = [
            ft.Container(
                content=ft.Text(
                    rotulo,
                    size=12,
                    weight=ft.FontWeight.W_600,
                    color=t.BRANCO if chave == urgencia[0] else t.TEXTO_SECUNDARIO,
                ),
                padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                bgcolor=t.CORES_URGENCIA[chave] if chave == urgencia[0] else t.BRANCO,
                border_radius=20,
                border=ft.Border.all(
                    1, t.CORES_URGENCIA[chave] if chave == urgencia[0] else t.BORDA
                ),
                on_click=lambda _, c=chave: selecionar_urgencia(c),
                expand=True,
                alignment=ft.Alignment.CENTER,
            )
            for chave, rotulo in NIVEIS_URGENCIA
        ]

    def selecionar_urgencia(chave: str) -> None:
        """Guarda o nível escolhido e atualiza a tela."""
        urgencia[0] = chave
        desenhar_urgencia()
        app.page.update()

    desenhar_urgencia()

    switch_emergencia = ft.Switch(
        label="Marcar como emergência",
        value=False,
        active_color=t.URGENCIA,
        label_text_style=ft.TextStyle(size=13, color=t.AZUL_INSTITUCIONAL),
    )

    def publicar(_: ft.ControlEvent) -> None:
        """Valida os campos e envia o pedido para a API."""
        titulo = (campo_titulo.value or "").strip()
        if len(titulo) < 3:
            app.aviso("Descreva em poucas palavras o que você precisa.", erro=True)
            return
        if not seletor_categoria.value:
            app.aviso("Escolha uma categoria.", erro=True)
            return

        try:
            pessoas = max(1, int(campo_pessoas.value or 1))
        except ValueError:
            app.aviso("Informe um número válido de pessoas.", erro=True)
            return

        criada = app.executar(
            lambda: app.api.criar_solicitacao(
                {
                    "titulo": titulo,
                    "descricao": campo_descricao.value or "",
                    "categoria_id": int(seletor_categoria.value),
                    "quantidade": campo_quantidade.value or "",
                    "urgencia": urgencia[0],
                    "pessoas_beneficiadas": pessoas,
                    "endereco": campo_endereco.value or "",
                    "emergencia": bool(switch_emergencia.value),
                }
            ),
            "Solicitação publicada! Já está visível para a comunidade.",
        )
        if criada is None:
            return

        app.substituir("detalhe_solicitacao", id=criada["id"])

    return ft.Column(
        [
            cabecalho("Nova solicitação", app.voltar),
            ft.Container(
                content=ft.Column(
                    [
                        t.subtitulo("Quanto mais claro o pedido, mais rápido alguém responde."),
                        campo_titulo,
                        seletor_categoria,
                        campo_descricao,
                        campo_quantidade,
                        campo_pessoas,
                        campo_endereco,
                        ft.Text(
                            "Nível de urgência",
                            size=13,
                            weight=ft.FontWeight.W_600,
                            color=t.AZUL_INSTITUCIONAL,
                        ),
                        linha_urgencia,
                        t.cartao(
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.CRISIS_ALERT, color=t.URGENCIA, size=20),
                                    ft.Column(
                                        [
                                            switch_emergencia,
                                            ft.Text(
                                                "Use apenas em situações de risco imediato.",
                                                size=11,
                                                color=t.TEXTO_SECUNDARIO,
                                            ),
                                        ],
                                        spacing=0,
                                        expand=True,
                                    ),
                                ],
                                spacing=10,
                            ),
                            cor="#FDECEC",
                            borda="#F5C9C9",
                        ),
                        ft.Container(height=4),
                        t.botao_primario("Publicar solicitação", publicar, ft.Icons.SEND, 400),
                        ft.Container(height=16),
                    ],
                    spacing=12,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
                padding=ft.Padding.symmetric(horizontal=16, vertical=14),
                expand=True,
                bgcolor=t.FUNDO_CLARO,
            ),
        ],
        spacing=0,
        expand=True,
    )
