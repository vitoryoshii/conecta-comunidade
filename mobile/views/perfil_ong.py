"""Tela 11 — Perfil da ONG."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from mobile import theme as t
from mobile.components.comuns import cabecalho

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App


def _card_recurso(recurso: dict[str, Any]) -> ft.Container:
    """Cartão de um recurso disponível na instituição."""
    return ft.Container(
        content=ft.Column(
            [
                t.icone_por_nome(recurso.get("icone", "inventory_2"), 20, t.VERDE_ESCURO),
                ft.Text(
                    str(recurso.get("quantidade", "—")),
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=t.AZUL_INSTITUCIONAL,
                ),
                ft.Text(
                    recurso.get("nome", ""),
                    size=11,
                    color=t.TEXTO_SECUNDARIO,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=2,
                ),
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=10, vertical=14),
        bgcolor=t.BRANCO,
        border_radius=14,
        border=ft.Border.all(1, t.BORDA),
        width=110,
    )


def _dialogo_avaliacao(app: App, ong_id: int) -> None:
    """Abre o seletor de estrelas para avaliar a instituição."""

    def avaliar(nota: int) -> None:
        """Envia a nota e recarrega o perfil com a média atualizada."""
        app.page.pop_dialog()
        if app.executar(lambda: app.api.avaliar_ong(ong_id, nota), "Obrigado pela avaliação!"):
            app.renderizar()

    app.page.show_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Text("Como foi sua experiência?", color=t.AZUL_INSTITUCIONAL),
            content=ft.Row(
                [
                    ft.IconButton(
                        ft.Icons.STAR_ROUNDED,
                        icon_color=t.AMARELO_ATENCAO,
                        icon_size=34,
                        tooltip=f"{nota} estrela(s)",
                        on_click=lambda _, n=nota: avaliar(n),
                    )
                    for nota in range(1, 6)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                tight=True,
            ),
            actions=[
                ft.TextButton(content="Cancelar", on_click=lambda _: app.page.pop_dialog())
            ],
        )
    )


def construir(app: App) -> ft.Control:
    """Monta o perfil completo da instituição."""
    ong_id = app.state.rota_atual.parametros.get("id")
    ong: dict[str, Any] | None = app.executar(
        lambda: app.api.obter_ong(ong_id, **app.coordenadas())
    )
    if ong is None:
        return t.area_vazia("Não foi possível carregar esta instituição.", t.ICONES["erro"])

    def acao_indisponivel(mensagem: str):
        """Ações que dependem de integrações fora do escopo desta versão."""
        return lambda _: app.aviso(mensagem)

    def falar_com_a_ong(_: ft.ControlEvent) -> None:
        """Orienta o contato — a conversa acontece via pedidos e propostas."""
        app.aviso(
            f"O contato com {ong['nome']} acontece pelos pedidos publicados. "
            "Abra uma solicitação e a instituição poderá responder."
        )

    recursos = ong.get("recursos_disponiveis") or []

    cabecalho_ong = t.cartao(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.CircleAvatar(
                            content=ft.Text(
                                ong["nome"][0].upper(),
                                size=22,
                                color=t.BRANCO,
                                weight=ft.FontWeight.BOLD,
                            ),
                            bgcolor=t.AZUL_INSTITUCIONAL,
                            radius=30,
                        ),
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text(
                                            ong["nome"],
                                            size=17,
                                            weight=ft.FontWeight.BOLD,
                                            color=t.AZUL_INSTITUCIONAL,
                                            expand=True,
                                        ),
                                        *([t.selo_verificada()] if ong.get("verificada") else []),
                                    ],
                                    spacing=6,
                                ),
                                t.estrelas(
                                    ong.get("avaliacao", 0.0), ong.get("total_avaliacoes"), 16
                                ),
                                ft.Row(
                                    [
                                        ft.Icon(
                                            t.ICONES["local"],
                                            size=13,
                                            color=t.TEXTO_SECUNDARIO,
                                        ),
                                        ft.Text(
                                            f"{ong.get('distancia_formatada', '--')} · "
                                            f"{ong.get('endereco', '')}",
                                            size=11,
                                            color=t.TEXTO_SECUNDARIO,
                                            max_lines=2,
                                            expand=True,
                                        ),
                                    ],
                                    spacing=4,
                                ),
                            ],
                            spacing=5,
                            expand=True,
                        ),
                    ],
                    spacing=14,
                ),
            ],
            spacing=10,
        )
    )

    return ft.Column(
        [
            cabecalho(
                "Perfil da instituição",
                app.voltar,
                [
                    ft.IconButton(
                        ft.Icons.STAR_OUTLINE_ROUNDED,
                        icon_color=t.AMARELO_ATENCAO,
                        tooltip="Avaliar",
                        on_click=lambda _: _dialogo_avaliacao(app, ong_id),
                    )
                ],
            ),
            ft.Container(
                content=ft.Column(
                    [
                        cabecalho_ong,
                        t.cartao(
                            ft.Column(
                                [
                                    ft.Text(
                                        "Sobre",
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color=t.AZUL_INSTITUCIONAL,
                                    ),
                                    ft.Text(
                                        ong.get("descricao") or "Sem descrição.",
                                        size=13,
                                        color=t.TEXTO_SECUNDARIO,
                                    ),
                                ],
                                spacing=6,
                            )
                        ),
                        ft.Text(
                            "Recursos disponíveis",
                            size=15,
                            weight=ft.FontWeight.BOLD,
                            color=t.AZUL_INSTITUCIONAL,
                        ),
                        (
                            ft.Row(
                                [_card_recurso(recurso) for recurso in recursos],
                                spacing=10,
                                scroll=ft.ScrollMode.AUTO,
                            )
                            if recursos
                            else t.subtitulo("Nenhum recurso cadastrado no momento.")
                        ),
                        ft.Container(height=6),
                        t.botao_primario(
                            "Solicitar ajuda",
                            lambda _: app.navegar("nova_solicitacao"),
                            t.ICONES["preciso_de_ajuda"],
                            400,
                        ),
                        t.botao_secundario(
                            "Doar recursos",
                            lambda _: app.navegar("nova_oferta"),
                            t.ICONES["doar"],
                            400,
                        ),
                        t.botao_secundario(
                            "Ser voluntário",
                            acao_indisponivel(
                                "Inscrição de voluntariado: procure a instituição pelo endereço acima."
                            ),
                            t.ICONES["voluntariado"],
                            400,
                            cor=t.AZUL_INSTITUCIONAL,
                        ),
                        t.botao_secundario(
                            "Falar com a ONG",
                            falar_com_a_ong,
                            t.ICONES["conversa"],
                            400,
                            cor=t.AZUL_INSTITUCIONAL,
                        ),
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
