"""Aba Mensagens — lista de conversas que dá acesso ao chat."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from mobile import theme as t
from mobile.components.comuns import cartao_conversa
from mobile.components.fab import ESPACO_PARA_O_FAB

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

VAZIO = (
    "Nenhuma conversa ainda.\n"
    "Quando você oferecer ou pedir ajuda, as conversas aparecem aqui."
)

SEM_RESULTADO = "Nenhuma conversa com esse nome."


def construir(app: App) -> ft.Control:
    """Monta a lista de conversas do usuário logado."""
    busca: str = app.state.rota_atual.parametros.get("busca", "")
    conversas: list[dict[str, Any]] = app.executar(lambda: app.api.listar_conversas()) or []

    # O filtro é local: a lista de conversas de uma pessoa é curta, e uma volta
    # à API a cada tecla digitada custaria mais do que percorrer a lista aqui.
    if busca:
        procurado = busca.strip().lower()
        visiveis = [
            conversa
            for conversa in conversas
            if procurado in (conversa.get("interlocutor_nome") or "").lower()
            or procurado in (conversa.get("solicitacao_titulo") or "").lower()
        ]
    else:
        visiveis = conversas

    def abrir(conversa: dict[str, Any]) -> None:
        """Abre o chat com o interlocutor escolhido."""
        app.navegar(
            "chat",
            com=conversa["interlocutor_id"],
            nome=conversa["interlocutor_nome"],
            solicitacao_id=conversa.get("solicitacao_id"),
            solicitacao_titulo=conversa.get("solicitacao_titulo"),
        )

    def filtrar(evento: ft.ControlEvent) -> None:
        """Reabre a tela com o texto buscado (sem crescer a pilha)."""
        app.substituir("conversas", busca=evento.control.value or "")

    campo_busca = ft.Container(
        content=ft.TextField(
            value=busca,
            hint_text="Buscar por nome ou pedido...",
            prefix_icon=t.ICONES["buscar"],
            filled=True,
            fill_color=t.BRANCO,
            border_radius=t.RAIO_BOTAO,
            border_color=t.TRANSPARENTE,
            focused_border_color=t.TRANSPARENTE,
            color=t.TEXTO_FORTE,
            hint_style=ft.TextStyle(size=13, color=t.TEXTO_SECUNDARIO),
            content_padding=ft.Padding.symmetric(horizontal=14, vertical=13),
            on_submit=filtrar,
        ),
        border_radius=t.RAIO_BOTAO,
        shadow=t.SOMBRA_CARD,
    )

    if visiveis:
        lista: ft.Control = ft.Column(
            [cartao_conversa(conversa, abrir) for conversa in visiveis], spacing=12
        )
    elif busca:
        lista = t.area_vazia(SEM_RESULTADO, t.ICONES["sem_resultado"])
    else:
        lista = t.area_vazia(VAZIO, t.ICONES["conversas"])

    total_nao_lidas = sum(conversa.get("nao_lidas", 0) for conversa in conversas)

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        t.titulo("Mensagens", 22),
                        (
                            t.etiqueta(
                                f"{total_nao_lidas} não lida"
                                + ("s" if total_nao_lidas != 1 else ""),
                                cor_texto=t.BRANCO,
                                cor_fundo=t.URGENCIA,
                            )
                            if total_nao_lidas
                            else ft.Container(width=0)
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                t.subtitulo("Converse com quem está ajudando ou pedindo ajuda."),
                campo_busca,
                lista,
                # Folga para a última conversa não terminar embaixo do FAB.
                ft.Container(height=ESPACO_PARA_O_FAB),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=16),
        expand=True,
        bgcolor=t.FUNDO_CLARO,
    )
