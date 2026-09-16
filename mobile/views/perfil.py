"""Tela 13 — Meu perfil (com "Meu impacto" e menu)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from mobile import theme as t

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

ROTULOS_TIPO = {
    "solicitante": "Solicitante",
    "doador": "Doador(a)",
    "voluntario": "Voluntário(a)",
    "ong": "Representante de ONG",
}


def _numero_impacto(valor: int, rotulo: str, icone: ft.IconData, cor: str) -> ft.Container:
    """Um dos três números da seção "Meu impacto"."""
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(icone, size=20, color=cor),
                ft.Text(str(valor), size=22, weight=ft.FontWeight.BOLD, color=t.AZUL_INSTITUCIONAL),
                ft.Text(
                    rotulo,
                    size=10,
                    color=t.TEXTO_SECUNDARIO,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=2,
                ),
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(vertical=14, horizontal=6),
        bgcolor=t.BRANCO,
        border_radius=14,
        border=ft.Border.all(1, t.BORDA),
        width=122,
    )


def _item_menu(
    icone: ft.IconData, rotulo: str, on_click, cor: str = t.AZUL_INSTITUCIONAL
) -> ft.Container:
    """Linha do menu inferior do perfil."""
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(icone, size=20, color=cor),
                ft.Text(rotulo, size=14, color=cor, expand=True),
                ft.Icon(t.ICONES["detalhe"], size=18, color=t.BORDA),
            ],
            spacing=14,
        ),
        padding=ft.Padding.symmetric(horizontal=14, vertical=14),
        on_click=on_click,
        ink=True,
    )


def construir(app: App) -> ft.Control:
    """Monta o perfil, os números de impacto e o menu de navegação."""
    usuario: dict[str, Any] = app.state.usuario or {}
    impacto = app.executar(lambda: app.api.impacto()) or {}

    def sair(_: ft.ControlEvent) -> None:
        """Encerra a sessão e volta à tela de abertura."""
        app.state.sair()
        app.api.definir_token(None)
        app.aviso("Você saiu da sua conta.")
        app.reiniciar("splash")

    def em_breve(mensagem: str):
        """Itens do menu que dependem de funcionalidades futuras."""
        return lambda _: app.aviso(mensagem)

    return ft.Container(
        content=ft.Column(
            [
                # --- Identificação ------------------------------------------
                t.cartao(
                    ft.Row(
                        [
                            ft.CircleAvatar(
                                content=ft.Text(
                                    (usuario.get("nome") or "?")[0].upper(),
                                    size=24,
                                    color=t.BRANCO,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                bgcolor=t.VERDE_PRIMARIO,
                                radius=32,
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        usuario.get("nome", "Visitante"),
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                        color=t.AZUL_INSTITUCIONAL,
                                    ),
                                    ft.Row(
                                        [
                                            ft.Icon(
                                                t.ICONES["local"],
                                                size=13,
                                                color=t.TEXTO_SECUNDARIO,
                                            ),
                                            ft.Text(
                                                usuario.get("cidade") or "Sem cidade definida",
                                                size=12,
                                                color=t.TEXTO_SECUNDARIO,
                                            ),
                                        ],
                                        spacing=4,
                                    ),
                                    t.etiqueta(
                                        ROTULOS_TIPO.get(
                                            usuario.get("tipo", ""), usuario.get("tipo", "")
                                        ),
                                        icone=t.ICONES["nome"],
                                    ),
                                ],
                                spacing=5,
                                expand=True,
                            ),
                        ],
                        spacing=14,
                    )
                ),
                # --- Meu impacto --------------------------------------------
                ft.Text(
                    "Meu impacto", size=16, weight=ft.FontWeight.BOLD, color=t.AZUL_INSTITUCIONAL
                ),
                ft.Row(
                    [
                        _numero_impacto(
                            impacto.get("solicitacoes_atendidas", 0),
                            "Solicitações atendidas",
                            t.ICONES["concluido"],
                            t.VERDE_PRIMARIO,
                        ),
                        _numero_impacto(
                            impacto.get("doacoes_recebidas", 0),
                            "Doações recebidas",
                            t.ICONES["doar"],
                            t.AZUL_INSTITUCIONAL,
                        ),
                        _numero_impacto(
                            impacto.get("acoes_voluntario", 0),
                            "Ações como voluntário",
                            t.ICONES["voluntariado"],
                            t.AMARELO_ATENCAO,
                        ),
                    ],
                    spacing=10,
                    wrap=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        t.etiqueta(
                            f"{impacto.get('total_solicitacoes_criadas', 0)} pedidos publicados",
                            icone=t.ICONES["pedido"],
                        ),
                        t.etiqueta(
                            f"{impacto.get('total_ofertas_criadas', 0)} ofertas enviadas",
                            icone=t.ICONES["doacoes"],
                        ),
                    ],
                    spacing=8,
                    wrap=True,
                ),
                # --- Menu ----------------------------------------------------
                ft.Container(height=4),
                t.cartao(
                    ft.Column(
                        [
                            _item_menu(
                                t.ICONES["pedido"],
                                "Minhas solicitações",
                                lambda _: app.navegar("minhas_solicitacoes"),
                            ),
                            ft.Divider(height=1, color=t.BORDA),
                            _item_menu(
                                t.ICONES["doar"],
                                "Minhas doações",
                                lambda _: app.navegar("explorar", aba="ofertas"),
                            ),
                            ft.Divider(height=1, color=t.BORDA),
                            _item_menu(
                                t.ICONES["doacoes"],
                                "Favoritos",
                                em_breve("Favoritos entram na próxima versão do app."),
                            ),
                            ft.Divider(height=1, color=t.BORDA),
                            _item_menu(
                                ft.Icons.STAR_OUTLINE_ROUNDED,
                                "Avaliações",
                                lambda _: app.navegar("ongs"),
                            ),
                            ft.Divider(height=1, color=t.BORDA),
                            _item_menu(
                                t.ICONES["configuracoes"],
                                "Configurações",
                                em_breve("Configurações entram na próxima versão do app."),
                            ),
                            ft.Divider(height=1, color=t.BORDA),
                            _item_menu(
                                t.ICONES["ajuda"],
                                "Ajuda",
                                em_breve(
                                    "Dúvidas? Documentação da API em http://127.0.0.1:8000/docs"
                                ),
                            ),
                            ft.Divider(height=1, color=t.BORDA),
                            _item_menu(t.ICONES["sair"], "Sair", sair, t.URGENCIA),
                        ],
                        spacing=0,
                    ),
                    padding=0,
                ),
                ft.Container(height=10),
                ft.Text(
                    "Conecta Comunidade · v1.0.0",
                    size=11,
                    color=t.BORDA,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=10),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=16),
        expand=True,
        bgcolor=t.FUNDO_CLARO,
    )
