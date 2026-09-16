"""
Componentes compartilhados entre as telas.

Cabeçalho, navegação inferior e os cartões de listagem (solicitação, oferta,
ONG e conversa). Centralizar esses blocos garante que o mesmo pedido apareça
exatamente igual na Home, em Explorar e em Minhas solicitações.
"""

from typing import Any, Callable

import flet as ft

from mobile import theme as t


# --------------------------------------------------------------------------- #
# Cabeçalho
# --------------------------------------------------------------------------- #
def cabecalho(
    titulo: str,
    ao_voltar: Callable[[Any], None] | None = None,
    acoes: list[ft.Control] | None = None,
    subtitulo: str | None = None,
) -> ft.Container:
    """Barra superior com título, botão de voltar opcional e ações."""
    esquerda: list[ft.Control] = []
    if ao_voltar is not None:
        esquerda.append(
            ft.IconButton(
                t.ICONES["voltar"],
                icon_color=t.AZUL_INSTITUCIONAL,
                on_click=ao_voltar,
                tooltip="Voltar",
            )
        )

    textos: list[ft.Control] = [
        ft.Text(titulo, size=18, weight=ft.FontWeight.BOLD, color=t.AZUL_INSTITUCIONAL)
    ]
    if subtitulo:
        textos.append(ft.Text(subtitulo, size=12, color=t.TEXTO_SECUNDARIO))

    esquerda.append(ft.Column(textos, spacing=0, expand=True))

    return ft.Container(
        content=ft.Row(
            [
                ft.Row(esquerda, spacing=4, expand=True),
                ft.Row(acoes or [], spacing=0, tight=True),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding.symmetric(horizontal=12, vertical=10),
        bgcolor=t.BRANCO,
        border=ft.Border.only(bottom=ft.BorderSide(1, t.BORDA)),
    )


# --------------------------------------------------------------------------- #
# Navegação inferior
# --------------------------------------------------------------------------- #
# Ordem das abas: Início · Explorar · Publicar (+) · Mensagens · Perfil.
# (rota, ícone inativo, ícone ativo, rótulo). O par sai sempre da MESMA família:
# contornado quando inativo, cheio/rounded quando ativo — é o que dá a leitura
# imediata de qual aba está selecionada sem depender só da cor.
ABAS = [
    ("home", ft.Icons.HOME_OUTLINED, ft.Icons.HOME_ROUNDED, "Início"),
    ("explorar", ft.Icons.SEARCH_OUTLINED, ft.Icons.SEARCH_ROUNDED, "Explorar"),
    ("publicar", ft.Icons.ADD_CIRCLE_OUTLINE, ft.Icons.ADD_CIRCLE_ROUNDED, "Publicar"),
    ("conversas", ft.Icons.CHAT_BUBBLE_OUTLINE, ft.Icons.CHAT_BUBBLE_ROUNDED, "Mensagens"),
    ("perfil", ft.Icons.PERSON_OUTLINE, ft.Icons.PERSON_ROUNDED, "Perfil"),
]


def navegacao_inferior(
    rota_ativa: str, ao_selecionar: Callable[[str], None], nao_lidas: int = 0
) -> ft.Container:
    """Barra inferior com o botão central "+" em destaque.

    Construímos a barra manualmente (em vez de usar `ft.NavigationBar`) porque o
    botão central precisa de tamanho, cor e elevação próprios — é a âncora
    visual do app.
    """
    itens: list[ft.Control] = []

    for rota, icone, icone_ativo, rotulo in ABAS:
        ativo = rota == rota_ativa

        if rota == "publicar":
            itens.append(
                ft.Container(
                    content=ft.Container(
                        content=ft.Icon(t.ICONES["adicionar"], color=t.BRANCO, size=t.ICONE_DESTAQUE),
                        width=54,
                        height=54,
                        bgcolor=t.VERDE_PRIMARIO,
                        border_radius=27,
                        alignment=ft.Alignment.CENTER,
                        shadow=ft.BoxShadow(
                            blur_radius=12, color="#332E9E5B", offset=ft.Offset(0, 4)
                        ),
                    ),
                    on_click=lambda _, r=rota: ao_selecionar(r),
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    tooltip="Publicar",
                )
            )
            continue

        cor = t.VERDE_PRIMARIO if ativo else t.TEXTO_SECUNDARIO
        icone_control: ft.Control = ft.Icon(
            icone_ativo if ativo else icone, size=t.ICONE_ACAO, color=cor
        )

        # Badge de mensagens não lidas sobre o ícone de conversas.
        if rota == "conversas" and nao_lidas > 0:
            icone_control = ft.Stack(
                [
                    icone_control,
                    ft.Container(
                        content=ft.Text(
                            str(nao_lidas) if nao_lidas < 10 else "9+",
                            size=9,
                            color=t.BRANCO,
                            weight=ft.FontWeight.BOLD,
                        ),
                        bgcolor=t.URGENCIA,
                        width=16,
                        height=16,
                        border_radius=8,
                        alignment=ft.Alignment.CENTER,
                        left=12,
                        top=-4,
                    ),
                ],
                width=32,
                height=24,
            )

        itens.append(
            ft.Container(
                content=ft.Column(
                    [icone_control, ft.Text(rotulo, size=10, color=cor)],
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                on_click=lambda _, r=rota: ao_selecionar(r),
                expand=True,
                padding=ft.Padding.symmetric(vertical=8),
                alignment=ft.Alignment.CENTER,
            )
        )

    return ft.Container(
        content=ft.Row(itens, alignment=ft.MainAxisAlignment.SPACE_EVENLY),
        bgcolor=t.BRANCO,
        padding=ft.Padding.symmetric(horizontal=4, vertical=4),
        border=ft.Border.only(top=ft.BorderSide(1, t.BORDA)),
    )


# --------------------------------------------------------------------------- #
# Cartões de listagem
# --------------------------------------------------------------------------- #
def metadado(icone: ft.IconData, texto: str) -> ft.Row:
    """Par ícone + texto que se mantém unido quando a linha quebra."""
    return ft.Row(
        [
            ft.Icon(icone, size=13, color=t.TEXTO_SECUNDARIO),
            ft.Text(texto, size=12, color=t.TEXTO_SECUNDARIO),
        ],
        spacing=4,
        tight=True,
    )


def cartao_solicitacao(
    solicitacao: dict[str, Any], ao_clicar: Callable[[int], None]
) -> ft.Container:
    """Cartão de pedido de ajuda: urgência, distância e tempo de publicação."""
    linha_superior: list[ft.Control] = [t.badge_urgencia(solicitacao.get("urgencia", "media"))]
    if solicitacao.get("emergencia"):
        linha_superior.insert(0, t.badge_emergencia())

    # Cada par ícone + texto vira uma Row "tight": assim, ao quebrar a linha, o
    # ícone nunca fica órfão do seu valor.
    metadados = ft.Row(
        [
            metadado(t.ICONES["local"], solicitacao.get("distancia_formatada", "--")),
            metadado(t.ICONES["horario"], solicitacao.get("tempo_publicacao", "")),
            metadado(
                t.ICONES["pessoas"],
                f"{solicitacao.get('pessoas_beneficiadas', 1)} pessoa(s)",
            ),
        ],
        spacing=12,
        run_spacing=4,
        wrap=True,
    )

    conteudo = ft.Row(
        [
            ft.Container(
                content=t.icone_por_nome(solicitacao.get("categoria_icone", "category"), 22),
                width=46,
                height=46,
                bgcolor=t.VERDE_SUAVE,
                border_radius=12,
                alignment=ft.Alignment.CENTER,
            ),
            ft.Column(
                [
                    ft.Row(linha_superior, spacing=6, wrap=True),
                    ft.Text(
                        solicitacao.get("titulo", ""),
                        size=15,
                        weight=ft.FontWeight.W_600,
                        color=t.AZUL_INSTITUCIONAL,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    metadados,
                ],
                spacing=6,
                expand=True,
            ),
            ft.Icon(t.ICONES["detalhe"], color=t.BORDA),
        ],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    return t.cartao(
        conteudo,
        on_click=lambda _: ao_clicar(solicitacao["id"]),
        borda=t.URGENCIA if solicitacao.get("emergencia") else None,
    )


ROTULOS_TIPO_AJUDA = {
    "tenho_item": "Tenho o item",
    "posso_entregar": "Posso entregar",
    "ponto_retirada": "Ponto de retirada",
}

ICONES_TIPO_AJUDA = {
    "tenho_item": t.ICONES["oferta"],
    "posso_entregar": t.ICONES["entrega"],
    "ponto_retirada": t.ICONES["ponto_retirada"],
}


def cartao_oferta(oferta: dict[str, Any], ao_clicar: Callable[[dict], None] | None = None):
    """Cartão de oferta: quem está doando, o quê e a que distância."""
    tipo = oferta.get("tipo_ajuda", "tenho_item")

    conteudo = ft.Row(
        [
            ft.Container(
                content=ft.Icon(
                    ICONES_TIPO_AJUDA.get(tipo, t.ICONES["doar"]),
                    size=22,
                    color=t.VERDE_ESCURO,
                ),
                width=46,
                height=46,
                bgcolor=t.VERDE_SUAVE,
                border_radius=12,
                alignment=ft.Alignment.CENTER,
            ),
            ft.Column(
                [
                    t.etiqueta(ROTULOS_TIPO_AJUDA.get(tipo, tipo)),
                    ft.Text(
                        oferta.get("titulo", ""),
                        size=15,
                        weight=ft.FontWeight.W_600,
                        color=t.AZUL_INSTITUCIONAL,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Row(
                        [
                            metadado(t.ICONES["nome"], oferta.get("autor_nome", "")),
                            metadado(
                                t.ICONES["local"],
                                oferta.get("distancia_formatada", "--"),
                            ),
                            metadado(t.ICONES["horario"], oferta.get("tempo_publicacao", "")),
                        ],
                        spacing=12,
                        run_spacing=4,
                        wrap=True,
                    ),
                ],
                spacing=6,
                expand=True,
            ),
        ],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    return t.cartao(
        conteudo, on_click=(lambda _: ao_clicar(oferta)) if ao_clicar else None
    )


def cartao_ong(ong: dict[str, Any], ao_clicar: Callable[[int], None]) -> ft.Container:
    """Cartão de instituição: avatar, avaliação, distância e selo."""
    titulo_linha: list[ft.Control] = [
        ft.Text(
            ong.get("nome", ""),
            size=15,
            weight=ft.FontWeight.W_600,
            color=t.AZUL_INSTITUCIONAL,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
            expand=True,
        )
    ]
    if ong.get("verificada"):
        titulo_linha.append(t.selo_verificada())

    conteudo = ft.Row(
        [
            ft.CircleAvatar(
                content=ft.Text(
                    ong.get("nome", "?")[0].upper(),
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=t.BRANCO,
                ),
                bgcolor=t.AZUL_INSTITUCIONAL,
                radius=24,
            ),
            ft.Column(
                [
                    ft.Row(titulo_linha, spacing=6),
                    t.estrelas(ong.get("avaliacao", 0.0), ong.get("total_avaliacoes")),
                    ft.Row(
                        [
                            ft.Icon(t.ICONES["local"], size=13, color=t.TEXTO_SECUNDARIO),
                            ft.Text(
                                ong.get("distancia_formatada", "--"),
                                size=12,
                                color=t.TEXTO_SECUNDARIO,
                            ),
                            ft.Text("·", size=12, color=t.BORDA),
                            ft.Text(
                                ong.get("endereco", ""),
                                size=12,
                                color=t.TEXTO_SECUNDARIO,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                expand=True,
                            ),
                        ],
                        spacing=4,
                    ),
                ],
                spacing=5,
                expand=True,
            ),
            ft.Icon(t.ICONES["detalhe"], color=t.BORDA),
        ],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    return t.cartao(conteudo, on_click=lambda _: ao_clicar(ong["id"]))


def cartao_conversa(
    conversa: dict[str, Any], ao_clicar: Callable[[dict], None]
) -> ft.Container:
    """Linha da aba Mensagens: interlocutor, última fala e não lidas."""
    nao_lidas = conversa.get("nao_lidas", 0)

    direita: list[ft.Control] = []
    if nao_lidas:
        direita.append(
            ft.Container(
                content=ft.Text(str(nao_lidas), size=11, color=t.BRANCO, weight=ft.FontWeight.BOLD),
                bgcolor=t.VERDE_PRIMARIO,
                width=22,
                height=22,
                border_radius=11,
                alignment=ft.Alignment.CENTER,
            )
        )

    conteudo = ft.Row(
        [
            ft.CircleAvatar(
                content=ft.Text(
                    conversa.get("interlocutor_nome", "?")[0].upper(),
                    color=t.BRANCO,
                    weight=ft.FontWeight.BOLD,
                ),
                bgcolor=t.VERDE_PRIMARIO,
                radius=22,
            ),
            ft.Column(
                [
                    ft.Text(
                        conversa.get("interlocutor_nome", ""),
                        size=15,
                        weight=ft.FontWeight.W_600,
                        color=t.AZUL_INSTITUCIONAL,
                    ),
                    ft.Text(
                        conversa.get("ultima_mensagem", ""),
                        size=12,
                        color=t.TEXTO_SECUNDARIO,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    *(
                        [
                            t.etiqueta(
                                conversa["solicitacao_titulo"], icone=t.ICONES["doacoes"]
                            )
                        ]
                        if conversa.get("solicitacao_titulo")
                        else []
                    ),
                ],
                spacing=4,
                expand=True,
            ),
            ft.Column(direita, horizontal_alignment=ft.CrossAxisAlignment.END, spacing=6),
        ],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    return t.cartao(conteudo, on_click=lambda _: ao_clicar(conversa))


def secao(titulo_texto: str, acao: ft.Control | None = None) -> ft.Row:
    """Cabeçalho de seção com um link de ação opcional à direita."""
    filhos: list[ft.Control] = [
        ft.Text(titulo_texto, size=16, weight=ft.FontWeight.BOLD, color=t.AZUL_INSTITUCIONAL)
    ]
    if acao is not None:
        filhos.append(acao)
    return ft.Row(filhos, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
