"""Tela de Ajuda e suporte.

Perguntas frequentes que abrem e fecham, um bloco de contato e os links para os
documentos legais. As respostas falam da plataforma como ela é hoje — inclusive
do que ela **não** faz (não entrega, não intermedia dinheiro), porque é isso que
evita expectativa errada logo no primeiro uso.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from mobile import theme as t
from mobile.components.comuns import cabecalho

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

CONTATO = "caio.cacalho@al.ibta.edu.br"

# (ícone, pergunta, resposta)
PERGUNTAS = [
    (
        ft.Icons.EDIT_NOTE_ROUNDED,
        "Como publico um pedido?",
        "Toque no botão + (canto inferior direito), escolha \"Preciso de ajuda\" e "
        "conte o que está faltando: categoria, quantidade e para quantas pessoas. "
        "Se for urgente, marque como emergência — o pedido vai para o topo das "
        "listas e ganha destaque no mapa.",
    ),
    (
        ft.Icons.LOCAL_SHIPPING_OUTLINED,
        "Como funciona a entrega?",
        "O aplicativo apenas aproxima as pessoas: quem oferece e quem precisa "
        "combinam local, horário e forma de entrega pelo chat. Nada é enviado, "
        "transportado ou garantido pela plataforma.",
    ),
    (
        ft.Icons.SHIELD_OUTLINED,
        "É seguro?",
        "Sua senha é guardada criptografada e seu CPF nunca aparece inteiro, nem "
        "para você. O perfil público não mostra CPF, telefone nem data de "
        "nascimento. Ainda assim, combine encontros em locais públicos, leve "
        "alguém junto quando puder e desconfie de quem pede dinheiro adiantado.",
    ),
    (
        ft.Icons.DIVERSITY_3_OUTLINED,
        "Como viro voluntário?",
        "No seu perfil, escolha o tipo \"Voluntário(a)\". Depois é só responder aos "
        "pedidos próximos com uma proposta — pode ser o item, o transporte ou um "
        "ponto de retirada.",
    ),
    (
        ft.Icons.VOLUNTEER_ACTIVISM_OUTLINED,
        "Como funcionam as doações?",
        "Você publica o que tem para doar e quem precisa entra em contato. O "
        "aplicativo não processa pagamentos nem recebe dinheiro: a doação é "
        "sempre direta entre as pessoas.",
    ),
]


def _pergunta(icone: ft.IconData, titulo: str, resposta: str) -> ft.Container:
    """Uma pergunta que expande ao ser tocada."""
    return t.cartao(
        ft.ExpansionTile(
            leading=ft.Container(
                content=ft.Icon(icone, size=17, color=t.VERDE_PRIMARIO),
                width=34,
                height=34,
                bgcolor=t.VERDE_SUAVE,
                border_radius=11,
                alignment=ft.Alignment.CENTER,
            ),
            title=ft.Text(
                titulo, size=13.5, weight=ft.FontWeight.W_600, color=t.TEXTO_FORTE
            ),
            # Sem a divisória padrão: quem separa os cartões é o espaçamento.
            controls=[
                ft.Container(
                    content=ft.Text(
                        resposta, size=12.5, color=t.TEXTO_SECUNDARIO, selectable=True
                    ),
                    padding=ft.Padding.only(left=16, right=16, bottom=14),
                )
            ],
            collapsed_shape=ft.RoundedRectangleBorder(radius=t.RAIO_CARD),
            shape=ft.RoundedRectangleBorder(radius=t.RAIO_CARD),
            icon_color=t.VERDE_PRIMARIO,
            collapsed_icon_color=t.TEXTO_INATIVO,
            text_color=t.TEXTO_FORTE,
            collapsed_text_color=t.TEXTO_FORTE,
        ),
        padding=0,
    )


def construir(app: App) -> ft.Control:
    """Monta o FAQ, o bloco de contato e os links legais."""

    def copiar(_: ft.ControlEvent) -> None:
        """Copia o e-mail de contato para a área de transferência."""
        app.page.clipboard.set(CONTATO)
        app.aviso("E-mail copiado. É só colar no seu aplicativo de e-mail.")

    def abrir_email(_: ft.ControlEvent) -> None:
        """Abre o aplicativo de e-mail com o destinatário preenchido."""
        app.page.launch_url(
            f"mailto:{CONTATO}?subject=Ajuda%20-%20Conecta%20Comunidade"
        )

    contato = t.cartao(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Icon(t.ICONES["email"], size=19, color=t.BRANCO),
                            width=40,
                            height=40,
                            border_radius=13,
                            alignment=ft.Alignment.CENTER,
                            gradient=ft.LinearGradient(
                                begin=ft.Alignment.TOP_LEFT,
                                end=ft.Alignment.BOTTOM_RIGHT,
                                colors=[t.TEAL, t.VERDE_PROFUNDO],
                            ),
                        ),
                        ft.Column(
                            [
                                t.titulo_cartao("Fale com a gente"),
                                t.meta("Respondemos em alguns dias úteis."),
                            ],
                            spacing=1,
                            expand=True,
                        ),
                    ],
                    spacing=12,
                ),
                ft.Container(
                    content=ft.Text(
                        CONTATO, size=12.5, color=t.TEXTO_FORTE, selectable=True
                    ),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                    bgcolor=t.CINZA_CLARO,
                    border_radius=t.RAIO_BOTAO,
                ),
                ft.Row(
                    [
                        t.botao_primario("Abrir e-mail", abrir_email, t.ICONES["enviar"], 170),
                        t.botao_secundario("Copiar", copiar, ft.Icons.COPY_ROUNDED, 130),
                    ],
                    spacing=10,
                    wrap=True,
                    run_spacing=8,
                ),
            ],
            spacing=12,
        )
    )

    legais = t.cartao(
        ft.Row(
            [
                ft.Icon(t.ICONES["documento"], size=18, color=t.AZUL_INSTITUCIONAL),
                ft.Text(
                    spans=[
                        ft.TextSpan("Consulte os "),
                        ft.TextSpan(
                            "Termos de Uso",
                            style=ft.TextStyle(
                                color=t.VERDE_PRIMARIO,
                                weight=ft.FontWeight.W_600,
                                decoration=ft.TextDecoration.UNDERLINE,
                            ),
                            on_click=lambda _: app.navegar(
                                "documento_legal", documento="termos"
                            ),
                        ),
                        ft.TextSpan(" e a "),
                        ft.TextSpan(
                            "Política de Privacidade",
                            style=ft.TextStyle(
                                color=t.VERDE_PRIMARIO,
                                weight=ft.FontWeight.W_600,
                                decoration=ft.TextDecoration.UNDERLINE,
                            ),
                            on_click=lambda _: app.navegar(
                                "documento_legal", documento="privacidade"
                            ),
                        ),
                        ft.TextSpan("."),
                    ],
                    size=12.5,
                    color=t.TEXTO_SECUNDARIO,
                    expand=True,
                ),
            ],
            spacing=10,
        )
    )

    corpo = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "Como podemos ajudar?",
                    size=17,
                    weight=ft.FontWeight.BOLD,
                    color=t.TEXTO_FORTE,
                    style=ft.TextStyle(letter_spacing=-0.4),
                ),
                t.subtitulo(
                    "As dúvidas mais comuns estão aqui. Se a sua não estiver, escreva "
                    "para a gente — a gente responde."
                ),
                ft.Container(height=2),
                *[_pergunta(icone, titulo, resposta) for icone, titulo, resposta in PERGUNTAS],
                ft.Container(height=4),
                contato,
                legais,
                ft.Container(height=20),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=16),
        expand=True,
        bgcolor=t.FUNDO_CLARO,
    )

    return ft.Column(
        [cabecalho("Ajuda e suporte", ao_voltar=app.voltar), corpo],
        spacing=0,
        expand=True,
    )
