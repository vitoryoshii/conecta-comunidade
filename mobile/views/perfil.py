"""Tela 13 — Meu perfil (com "Meu impacto" e menu)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from mobile import avatares
from mobile import theme as t
from mobile.components.avatar import avatar
from mobile.components.fab import ESPACO_PARA_O_FAB

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

ROTULOS_TIPO = {
    "solicitante": "Solicitante",
    "doador": "Doador(a)",
    "voluntario": "Voluntário(a)",
    "ong": "Representante de ONG",
}

LADO_DO_AVATAR = 82


def _cartao_impacto(valor: int, rotulo: str, icone: ft.IconData, cor: str) -> ft.Container:
    """Um dos três números da seção "Meu impacto".

    `expand=True` no lugar da largura fixa que existia antes: com três larguras
    de 122px em 430px de tela, o terceiro cartão saía da linha e aparecia
    cortado. Expandindo, os três dividem a largura disponível, seja qual for.
    """
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(icone, size=18, color=cor),
                ft.Text(
                    str(valor),
                    size=26,
                    weight=ft.FontWeight.BOLD,
                    color=t.TEXTO_FORTE,
                    style=ft.TextStyle(letter_spacing=-0.8),
                ),
                ft.Text(
                    rotulo,
                    size=10,
                    color=t.TEXTO_SECUNDARIO,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=2,
                ),
            ],
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(vertical=14, horizontal=6),
        bgcolor=t.BRANCO,
        border_radius=t.RAIO_CARD,
        shadow=t.SOMBRA_CARD,
        expand=True,
    )


def _item_menu(
    icone: ft.IconData,
    rotulo: str,
    on_click,
    destrutivo: bool = False,
) -> ft.Container:
    """Linha do menu: ícone em quadradinho suave, rótulo e chevron.

    Todas as linhas usam o mesmo par de cores (`t.MENU_ICONE` sobre
    `t.MENU_ICONE_FUNDO`). A única exceção é `destrutivo`, o Sair: ali o
    vermelho tem função — é o que faz a saída saltar da lista em vez de ser
    mais um item igual aos outros.
    """
    cor = t.MENU_ICONE_SAIDA if destrutivo else t.MENU_ICONE
    fundo = t.MENU_ICONE_FUNDO_SAIDA if destrutivo else t.MENU_ICONE_FUNDO
    cor_texto = t.URGENCIA if destrutivo else t.TEXTO_FORTE

    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(icone, size=17, color=cor),
                    width=34,
                    height=34,
                    bgcolor=fundo,
                    border_radius=11,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Text(
                    rotulo,
                    size=13.5,
                    weight=ft.FontWeight.W_500,
                    color=cor_texto,
                    expand=True,
                ),
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


def _identificacao(app: App, usuario: dict[str, Any]) -> ft.Container:
    """Avatar grande com botão de trocar a foto, nome, cidade e tipo."""

    async def trocar_foto(_: ft.ControlEvent) -> None:
        """Escolhe uma imagem e a grava como avatar do usuário.

        O `FilePicker` do Flet 0.86 é um *service*: basta criá-lo dentro do
        handler (ele se registra na página sozinho) e aguardar `pick_files`.
        """
        seletor = ft.FilePicker()
        escolhidos = await seletor.pick_files(
            dialog_title="Escolha sua foto de perfil",
            file_type=ft.FilePickerFileType.IMAGE,
            allow_multiple=False,
        )
        if not escolhidos:
            return

        origem = escolhidos[0].path
        if not origem:
            # No navegador o Flet não entrega o caminho local do arquivo.
            app.aviso("Trocar a foto só funciona no aplicativo instalado.", erro=True)
            return

        try:
            caminho = avatares.salvar(int(usuario.get("id", 0)), origem)
        except (ValueError, OSError) as erro:
            app.aviso(str(erro) or "Não foi possível salvar a imagem.", erro=True)
            return

        atualizado = app.executar(lambda: app.api.atualizar_perfil({"avatar_url": caminho}))
        if atualizado is None:
            return

        app.state.atualizar_usuario(atualizado)
        app.aviso("Foto de perfil atualizada.")
        app.renderizar()

    botao_camera = ft.Container(
        content=ft.Icon(ft.Icons.PHOTO_CAMERA_ROUNDED, size=15, color=t.BRANCO),
        width=30,
        height=30,
        bgcolor=t.VERDE_PRIMARIO,
        border_radius=15,
        alignment=ft.Alignment.CENTER,
        border=ft.Border.all(2.5, t.BRANCO),
        on_click=trocar_foto,
        ink=True,
        tooltip="Trocar foto",
        right=0,
        bottom=0,
        # A API ainda não oferece upload autenticado/storage público. No web,
        # esconder a ação evita prometer um envio que não pode ser persistido.
        visible=not bool(getattr(app.page, "web", False)),
    )

    return ft.Container(
        content=ft.Row(
            [
                ft.Stack(
                    [avatar(usuario, LADO_DO_AVATAR), botao_camera],
                    width=LADO_DO_AVATAR,
                    height=LADO_DO_AVATAR,
                ),
                ft.Column(
                    [
                        t.titulo(usuario.get("nome", "Visitante"), 19),
                        ft.Row(
                            [
                                ft.Icon(t.ICONES["local"], size=14, color=t.VERDE_PRIMARIO),
                                t.meta(
                                    ", ".join(
                                        p
                                        for p in (usuario.get("cidade"), usuario.get("estado"))
                                        if p
                                    )
                                    or "Sem cidade definida"
                                ),
                            ],
                            spacing=5,
                        ),
                        ft.Container(height=2),
                        t.etiqueta(
                            ROTULOS_TIPO.get(usuario.get("tipo", ""), usuario.get("tipo", "")),
                            icone=t.ICONES["participacao"],
                        ),
                    ],
                    spacing=4,
                    expand=True,
                ),
            ],
            spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(vertical=4),
    )


def construir(app: App) -> ft.Control:
    """Monta o perfil, os números de impacto e o menu de navegação."""
    usuario: dict[str, Any] = app.state.usuario or {}
    impacto = app.executar(lambda: app.api.impacto()) or {}

    async def sair(_: ft.ControlEvent) -> None:
        """Encerra a sessão e volta à tela de abertura."""
        app.state.sair()
        app.api.definir_token(None)
        await app._remover_token_persistido()
        app.aviso("Você saiu da sua conta.")
        app.reiniciar("login")

    # Só (ícone, rótulo, ação): a cor não é mais escolha de cada item.
    menu = [
        (ft.Icons.EDIT_OUTLINED, "Editar perfil", lambda _: app.navegar("editar_perfil")),
        (t.ICONES["pedido"], "Minhas solicitações", lambda _: app.navegar("minhas_solicitacoes")),
        (t.ICONES["doar"], "Minhas doações", lambda _: app.navegar("explorar", aba="ofertas")),
        (ft.Icons.FAVORITE_BORDER_ROUNDED, "Favoritos", lambda _: app.navegar("favoritos")),
        (ft.Icons.STAR_OUTLINE_ROUNDED, "Avaliações", lambda _: app.navegar("ongs")),
        (t.ICONES["configuracoes"], "Configurações", lambda _: app.navegar("configuracoes")),
        (t.ICONES["ajuda"], "Ajuda e suporte", lambda _: app.navegar("ajuda")),
    ]

    return ft.Container(
        content=ft.Column(
            [
                _identificacao(app, usuario),
                # --- Meu impacto --------------------------------------------
                t.titulo_secao("Meu impacto"),
                ft.Row(
                    [
                        _cartao_impacto(
                            impacto.get("solicitacoes_atendidas", 0),
                            "Solicitações atendidas",
                            t.ICONES["concluido"],
                            t.VERDE_PRIMARIO,
                        ),
                        _cartao_impacto(
                            impacto.get("doacoes_recebidas", 0),
                            "Doações recebidas",
                            t.ICONES["doar"],
                            t.TEAL,
                        ),
                        _cartao_impacto(
                            impacto.get("acoes_voluntario", 0),
                            "Ações como voluntário",
                            t.ICONES["voluntariado"],
                            t.AMARELO_ATENCAO,
                        ),
                    ],
                    spacing=10,
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
                    run_spacing=8,
                ),
                # --- Menu ----------------------------------------------------
                ft.Container(height=2),
                t.cartao(
                    ft.Column(
                        [_item_menu(*item) for item in menu],
                        spacing=0,
                    ),
                    padding=4,
                ),
                # Sair fica em um cartão à parte: é a única ação destrutiva da
                # tela, e separá-la evita o toque errado no fim da lista.
                t.cartao(
                    _item_menu(t.ICONES["sair"], "Sair", sair, destrutivo=True),
                    padding=4,
                ),
                ft.Container(height=6),
                ft.Text(
                    "Conecta Comunidade · v1.0.0",
                    size=11,
                    color=t.TEXTO_INATIVO,
                    text_align=ft.TextAlign.CENTER,
                ),
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
