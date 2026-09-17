"""Tela 6 — Detalhe da solicitação."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from mobile import theme as t
from mobile.components.avatar import avatar
from mobile.components.comuns import cabecalho, quadrado_de_categoria

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

ROTULOS_STATUS = {
    "ativa": "Ativa",
    "em_andamento": "Em andamento",
    "concluida": "Concluída",
}


def _galeria(fotos: list[str]) -> ft.Control:
    """Carrossel horizontal de fotos do pedido.

    Sem fotos, mostramos um espaço reservado — as solicitações do seed nascem
    sem imagem e a tela não pode ficar quebrada por isso.
    """
    if not fotos:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(t.ICONES["imagem"], size=34, color=t.BORDA),
                    ft.Text("Sem fotos anexadas", size=12, color=t.TEXTO_SECUNDARIO),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
            ),
            height=140,
            bgcolor=t.CINZA_CLARO,
            border_radius=t.RAIO,
            alignment=ft.Alignment.CENTER,
        )

    return ft.Row(
        [
            ft.Image(
                src=url,
                width=200,
                height=140,
                fit=ft.BoxFit.COVER,
                border_radius=t.RAIO,
                error_content=ft.Container(
                    content=ft.Icon(ft.Icons.BROKEN_IMAGE_OUTLINED, color=t.BORDA),
                    width=200,
                    height=140,
                    bgcolor=t.CINZA_CLARO,
                    border_radius=t.RAIO,
                    alignment=ft.Alignment.CENTER,
                ),
            )
            for url in fotos
        ],
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
    )


def _informacao(icone: ft.IconData, rotulo: str, valor: str) -> ft.Container:
    """Bloco compacto de informação usado na faixa de dados do pedido."""
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(icone, size=18, color=t.VERDE_PRIMARIO),
                ft.Text(
                    valor,
                    size=15,
                    weight=ft.FontWeight.BOLD,
                    color=t.TEXTO_FORTE,
                    style=ft.TextStyle(letter_spacing=-0.3),
                ),
                ft.Text(rotulo, size=10, color=t.TEXTO_SECUNDARIO),
            ],
            spacing=3,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(vertical=14),
        bgcolor=t.BRANCO,
        border_radius=t.RAIO_CARD,
        shadow=t.SOMBRA_CARD,
        expand=True,
    )


def construir(app: App) -> ft.Control:
    """Monta o detalhe completo de um pedido de ajuda."""
    solicitacao_id = app.state.rota_atual.parametros.get("id")

    dados: dict[str, Any] | None = app.executar(
        lambda: app.api.obter_solicitacao(solicitacao_id, **app.coordenadas())
    )
    if dados is None:
        return t.area_vazia("Não foi possível carregar esta solicitação.", t.ICONES["erro"])

    eh_meu_pedido = app.state.usuario_id == dados["usuario_id"]

    def compartilhar(_: ft.ControlEvent) -> None:
        """Copia um resumo do pedido para a área de transferência."""
        resumo = (
            f"{dados['titulo']} — {dados.get('endereco', '')}\n"
            f"Ajude pelo app Conecta Comunidade."
        )
        app.page.clipboard.set(resumo)
        app.aviso("Resumo copiado! Agora é só colar onde quiser.")

    def querer_ajudar(_: ft.ControlEvent) -> None:
        """Abre a tela de proposta (exige sessão ativa)."""
        if not app.state.autenticado:
            app.aviso("Entre na sua conta para enviar uma proposta.", erro=True)
            app.reiniciar("login")
            return
        app.navegar("quero_ajudar", solicitacao=dados)

    # --- Cabeçalho do conteúdo -------------------------------------------
    marcadores: list[ft.Control] = [t.badge_urgencia(dados.get("urgencia", "media"))]
    if dados.get("emergencia"):
        marcadores.insert(0, t.badge_emergencia())
    marcadores.append(
        t.etiqueta(ROTULOS_STATUS.get(dados.get("status", ""), dados.get("status", "")))
    )
    marcadores.append(
        t.etiqueta(dados.get("categoria_nome", ""), icone=t.ICONES["categoria"])
    )

    acoes: list[ft.Control] = []
    if not eh_meu_pedido:
        acoes.append(
            t.botao_primario("Quero ajudar", querer_ajudar, t.ICONES["doacoes"], 400)
        )
    else:
        acoes.append(
            t.botao_secundario(
                "Gerenciar meus pedidos",
                lambda _: app.navegar("minhas_solicitacoes"),
                t.ICONES["filtrar"],
                400,
            )
        )
    acoes.append(
        t.botao_secundario("Compartilhar", compartilhar, t.ICONES["compartilhar"], 400,
                           cor=t.TEXTO_FORTE)
    )

    corpo = ft.Column(
        [
            _galeria(dados.get("fotos") or []),
            ft.Row(
                [
                    quadrado_de_categoria(dados.get("categoria_icone"), 52),
                    ft.Column(
                        [
                            ft.Row(marcadores, spacing=6, wrap=True, run_spacing=4),
                            t.titulo(dados["titulo"], 20),
                        ],
                        spacing=8,
                        expand=True,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Row(
                [
                    avatar({"nome": dados.get("autor_nome")}, 30, com_sombra=False),
                    t.meta(
                        f"{dados.get('autor_nome', '')} · {dados.get('tempo_publicacao', '')}"
                    ),
                ],
                spacing=8,
            ),
            ft.Container(height=4),
            ft.Row(
                [
                    _informacao(
                        t.ICONES["local"],
                        "distância",
                        dados.get("distancia_formatada", "--"),
                    ),
                    _informacao(
                        t.ICONES["pessoas"],
                        "beneficiadas",
                        str(dados.get("pessoas_beneficiadas", 1)),
                    ),
                    _informacao(
                        t.ICONES["oferta"],
                        "quantidade",
                        dados.get("quantidade") or "—",
                    ),
                ],
                spacing=10,
            ),
            ft.Container(height=4),
            t.cartao(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(t.ICONES["descricao"], size=16, color=t.VERDE_PRIMARIO),
                                t.titulo("Descrição", 14),
                            ],
                            spacing=6,
                        ),
                        ft.Text(
                            dados.get("descricao") or "Sem descrição adicional.",
                            size=13,
                            color=t.TEXTO_SECUNDARIO,
                        ),
                    ],
                    spacing=6,
                )
            ),
            t.cartao(
                ft.Row(
                    [
                        ft.Icon(t.ICONES["local"], color=t.VERDE_PRIMARIO),
                        ft.Column(
                            [
                                t.titulo_cartao(
                                    dados.get("endereco") or "Endereço não informado"
                                ),
                                ft.Text(
                                    f"A {dados.get('distancia_formatada', '--')} de você · "
                                    f"{dados.get('latitude', 0):.4f}, {dados.get('longitude', 0):.4f}",
                                    size=11,
                                    color=t.TEXTO_SECUNDARIO,
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.IconButton(
                            t.ICONES["estado"],
                            icon_color=t.VERDE_PRIMARIO,
                            tooltip="Ver no mapa",
                            on_click=lambda _: app.navegar("mapa"),
                        ),
                    ],
                    spacing=10,
                )
            ),
            ft.Container(height=6),
            *acoes,
            ft.Container(height=16),
        ],
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    return ft.Column(
        [
            cabecalho(
                "Detalhe da solicitação",
                app.voltar,
                [
                    ft.IconButton(
                        t.ICONES["compartilhar"],
                        icon_color=t.TEXTO_FORTE,
                        on_click=compartilhar,
                        tooltip="Compartilhar",
                    )
                ],
            ),
            ft.Container(
                content=corpo,
                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                expand=True,
                bgcolor=t.FUNDO_CLARO,
            ),
        ],
        spacing=0,
        expand=True,
    )
