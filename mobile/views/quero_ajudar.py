"""Tela 7 — Quero ajudar (envio da proposta)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from mobile import theme as t
from mobile.components.comuns import cabecalho

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

# As três formas de ajudar previstas no domínio, com uma explicação curta.
OPCOES = [
    (
        "tenho_item",
        "Tenho o item",
        "Já tenho o que está sendo pedido e posso separar.",
        t.ICONES["oferta"],
    ),
    (
        "posso_entregar",
        "Posso entregar",
        "Tenho transporte e levo a doação até o local.",
        t.ICONES["entrega"],
    ),
    (
        "ponto_retirada",
        "Ofereço ponto de retirada",
        "Deixo em um endereço fixo para quem quiser buscar.",
        t.ICONES["ponto_retirada"],
    ),
]


def construir(app: App) -> ft.Control:
    """Formulário de proposta: tipo de ajuda + mensagem opcional."""
    solicitacao: dict[str, Any] = app.state.rota_atual.parametros.get("solicitacao", {})

    # O tipo escolhido vive em uma lista mutável para ser lido dentro do handler.
    escolhido = ["tenho_item"]

    campo_mensagem = t.campo(
        "Mensagem para quem pediu (opcional)",
        multilinha=True,
        dica="Ex.: consigo levar hoje à tarde, por volta das 15h.",
    )

    opcoes_coluna = ft.Column(spacing=10)

    def desenhar_opcoes() -> None:
        """Redesenha os cartões de escolha marcando o selecionado."""
        opcoes_coluna.controls = [
            _cartao_opcao(chave, titulo, descricao, icone, escolhido[0] == chave, selecionar)
            for chave, titulo, descricao, icone in OPCOES
        ]

    def selecionar(chave: str) -> None:
        """Marca a opção clicada e atualiza a tela."""
        escolhido[0] = chave
        desenhar_opcoes()
        app.page.update()

    desenhar_opcoes()

    def enviar(_: ft.ControlEvent) -> None:
        """Cria a oferta e, em seguida, abre o chat com o solicitante."""
        payload = {
            "titulo": f"Ajuda para: {solicitacao.get('titulo', 'solicitação')}",
            "descricao": campo_mensagem.value or "",
            "categoria_id": solicitacao.get("categoria_id"),
            "tipo_ajuda": escolhido[0],
            "solicitacao_id": solicitacao.get("id"),
            "mensagem": (campo_mensagem.value or "").strip() or None,
        }

        resposta = app.executar(
            lambda: app.api.criar_oferta(payload), "Proposta enviada! Agora é só combinar."
        )
        if resposta is None:
            return

        # A proposta abre a conversa com quem publicou o pedido.
        app.substituir(
            "chat",
            com=solicitacao.get("usuario_id"),
            nome=solicitacao.get("autor_nome", "Solicitante"),
            solicitacao_id=solicitacao.get("id"),
            solicitacao_titulo=solicitacao.get("titulo"),
        )

    return ft.Column(
        [
            cabecalho("Quero ajudar", app.voltar, subtitulo=solicitacao.get("titulo", "")),
            ft.Container(
                content=ft.Column(
                    [
                        t.cartao(
                            ft.Row(
                                [
                                    t.icone_por_nome(
                                        solicitacao.get("categoria_icone", "category"), 20
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text(
                                                solicitacao.get("titulo", ""),
                                                size=14,
                                                weight=ft.FontWeight.W_600,
                                                color=t.AZUL_INSTITUCIONAL,
                                            ),
                                            ft.Text(
                                                f"{solicitacao.get('quantidade') or '—'} · "
                                                f"{solicitacao.get('distancia_formatada', '--')} "
                                                "de você",
                                                size=12,
                                                color=t.TEXTO_SECUNDARIO,
                                            ),
                                        ],
                                        spacing=2,
                                        expand=True,
                                    ),
                                ],
                                spacing=10,
                            ),
                            cor=t.VERDE_SUAVE,
                            borda=t.VERDE_SUAVE,
                        ),
                        ft.Container(height=4),
                        ft.Text(
                            "Como você pode ajudar?",
                            size=15,
                            weight=ft.FontWeight.BOLD,
                            color=t.AZUL_INSTITUCIONAL,
                        ),
                        opcoes_coluna,
                        ft.Container(height=4),
                        campo_mensagem,
                        ft.Container(height=6),
                        t.botao_primario("Enviar proposta", enviar, t.ICONES["enviar"], 400),
                        ft.Row(
                            [
                                ft.Icon(
                                    t.ICONES["senha"], size=13, color=t.TEXTO_SECUNDARIO
                                ),
                                ft.Text(
                                    "Seus dados de contato só aparecem no chat.",
                                    size=11,
                                    color=t.TEXTO_SECUNDARIO,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=6,
                        ),
                    ],
                    spacing=10,
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


def _cartao_opcao(
    chave: str,
    titulo: str,
    descricao: str,
    icone: ft.IconData,
    selecionado: bool,
    ao_clicar,
) -> ft.Container:
    """Cartão selecionável de tipo de ajuda."""
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(
                        icone, size=20, color=t.BRANCO if selecionado else t.VERDE_ESCURO
                    ),
                    width=42,
                    height=42,
                    bgcolor=t.VERDE_PRIMARIO if selecionado else t.VERDE_SUAVE,
                    border_radius=12,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column(
                    [
                        ft.Text(
                            titulo,
                            size=14,
                            weight=ft.FontWeight.W_600,
                            color=t.AZUL_INSTITUCIONAL,
                        ),
                        ft.Text(descricao, size=11, color=t.TEXTO_SECUNDARIO),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Icon(
                    t.ICONES["sucesso"] if selecionado else ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED,
                    color=t.VERDE_PRIMARIO if selecionado else t.BORDA,
                ),
            ],
            spacing=12,
        ),
        padding=14,
        bgcolor=t.BRANCO,
        border_radius=t.RAIO,
        border=ft.Border.all(1.6 if selecionado else 1, t.VERDE_PRIMARIO if selecionado else t.BORDA),
        on_click=lambda _: ao_clicar(chave),
        ink=True,
    )
