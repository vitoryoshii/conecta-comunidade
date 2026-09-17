"""Tela de Configurações.

Quatro grupos: Conta, Notificações, Privacidade e Sobre. Cada grupo é um cartão
branco, e cada linha tem ícone em quadradinho, rótulo e o que ela faz à direita
— chevron quando abre outra tela, interruptor quando é uma preferência.

As preferências de notificação são gravadas de verdade (`PATCH /usuarios/me`),
para que o interruptor represente uma escolha. O que ainda **não** existe é o
envio: nada no app dispara push ou e-mail hoje, e a tela diz isso em vez de
prometer o que não acontece.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from mobile import theme as t
from mobile.components.comuns import cabecalho

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

VERSAO = "1.0.0"
CONTATO = "caio.cacalho@al.ibta.edu.br"

# (campo na API, rótulo, explicação curta)
NOTIFICACOES = [
    (
        "notificar_solicitacoes",
        "Novas solicitações próximas",
        "Quando alguém pede ajuda perto de você",
    ),
    ("notificar_mensagens", "Mensagens", "Quando recebe uma mensagem no chat"),
    ("notificar_atualizacoes", "Atualizações", "Novidades e avisos do aplicativo"),
]


def _grupo(titulo: str, linhas: list[ft.Control]) -> ft.Column:
    """Título de seção + cartão branco com as linhas do grupo."""
    return ft.Column(
        [
            t.titulo_secao(titulo),
            t.cartao(ft.Column(linhas, spacing=0), padding=4),
        ],
        spacing=8,
    )


def _quadradinho(icone: ft.IconData, cor: str) -> ft.Container:
    """Ícone da linha, no quadrado suave que o menu do Perfil usa."""
    return ft.Container(
        content=ft.Icon(icone, size=17, color=cor),
        width=34,
        height=34,
        bgcolor=f"{cor}1A",
        border_radius=11,
        alignment=ft.Alignment.CENTER,
    )


def _linha(
    icone: ft.IconData,
    rotulo: str,
    on_click,
    cor: str = t.VERDE_PRIMARIO,
    descricao: str | None = None,
) -> ft.Container:
    """Linha que abre outra tela (termina em chevron)."""
    textos: list[ft.Control] = [
        ft.Text(rotulo, size=13.5, weight=ft.FontWeight.W_500, color=t.TEXTO_FORTE)
    ]
    if descricao:
        textos.append(t.meta(descricao))

    return ft.Container(
        content=ft.Row(
            [
                _quadradinho(icone, cor),
                ft.Column(textos, spacing=1, expand=True),
                ft.Icon(t.ICONES["detalhe"], size=18, color=t.TEXTO_INATIVO),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=14, vertical=11),
        on_click=on_click,
        ink=True,
        border_radius=t.RAIO_CARD,
    )


def construir(app: App) -> ft.Control:
    """Monta a tela de configurações."""
    usuario: dict[str, Any] = app.state.usuario or {}
    # As preferências são do titular, então vêm de `/auth/me` (o perfil da
    # sessão é o schema público e não as carrega).
    privado: dict[str, Any] = app.executar(lambda: app.api.eu()) or {}

    def alternar(campo: str):
        """Grava a preferência assim que o interruptor muda."""

        def handler(evento: ft.ControlEvent) -> None:
            ligado = bool(evento.control.value)
            atualizado = app.executar(lambda: app.api.atualizar_perfil({campo: ligado}))
            if atualizado is None:
                # Falhou: o interruptor volta para onde estava, para não mentir
                # sobre o que está gravado.
                evento.control.value = not ligado
                app.page.update()
                return
            privado[campo] = ligado
            app.page.update()

        return handler

    interruptores = [
        ft.Container(
            content=ft.Row(
                [
                    _quadradinho(ft.Icons.NOTIFICATIONS_NONE_ROUNDED, t.VERDE_PRIMARIO),
                    ft.Column(
                        [
                            ft.Text(
                                rotulo,
                                size=13.5,
                                weight=ft.FontWeight.W_500,
                                color=t.TEXTO_FORTE,
                            ),
                            t.meta(descricao),
                        ],
                        spacing=1,
                        expand=True,
                    ),
                    ft.Switch(
                        value=bool(privado.get(campo, True)),
                        on_change=alternar(campo),
                        active_color=t.VERDE_PRIMARIO,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=14, vertical=6),
        )
        for campo, rotulo, descricao in NOTIFICACOES
    ]

    corpo = ft.Container(
        content=ft.Column(
            [
                _grupo(
                    "Conta",
                    [
                        _linha(
                            t.ICONES["nome"],
                            "Editar perfil",
                            lambda _: app.navegar("editar_perfil"),
                            descricao=usuario.get("email", ""),
                        ),
                        _linha(
                            t.ICONES["senha"],
                            "Alterar senha",
                            lambda _: app.navegar("alterar_senha"),
                            descricao="Pedimos sua senha atual para confirmar",
                        ),
                    ],
                ),
                _grupo("Notificações", interruptores),
                t.ajuda_clara(
                    "Suas escolhas ficam guardadas. O envio de avisos ainda não está "
                    "ligado nesta versão do aplicativo.",
                    icone=t.ICONES["info"],
                ),
                _grupo(
                    "Privacidade",
                    [
                        _linha(
                            t.ICONES["privacidade"],
                            "Política de Privacidade",
                            lambda _: app.navegar("documento_legal", documento="privacidade"),
                            cor=t.AZUL_INSTITUCIONAL,
                        ),
                        _linha(
                            t.ICONES["documento"],
                            "Termos de Uso",
                            lambda _: app.navegar("documento_legal", documento="termos"),
                            cor=t.AZUL_INSTITUCIONAL,
                        ),
                    ],
                ),
                _grupo(
                    "Sobre",
                    [
                        _linha(
                            t.ICONES["info"],
                            f"Conecta Comunidade v{VERSAO}",
                            lambda _: app.aviso(
                                "Projeto acadêmico — Centro Universitário UNIBTA."
                            ),
                            cor=t.TEAL,
                            descricao="Projeto acadêmico de Sistemas de Informação",
                        ),
                        _linha(
                            t.ICONES["ajuda"],
                            "Ajuda e contato",
                            lambda _: app.navegar("ajuda"),
                            cor=t.AMARELO_ATENCAO,
                            descricao=CONTATO,
                        ),
                    ],
                ),
                ft.Container(height=20),
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=16),
        expand=True,
        bgcolor=t.FUNDO_CLARO,
    )

    return ft.Column(
        [cabecalho("Configurações", ao_voltar=app.voltar), corpo],
        spacing=0,
        expand=True,
    )
