"""
Componentes compartilhados entre as telas.

Cabeçalho e cartões de listagem (solicitação, oferta, ONG e conversa).
Centralizar esses blocos garante que o mesmo pedido apareça exatamente igual na
Home, em Explorar e em Minhas solicitações. A barra inferior e o FAB moraram
aqui um tempo; hoje têm arquivo próprio (`nav_bar.py` e `fab.py`).
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
                icon_color=t.TEXTO_FORTE,
                on_click=ao_voltar,
                tooltip="Voltar",
            )
        )

    textos: list[ft.Control] = [t.titulo(titulo, 18)]
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
        # Sombra curta para baixo no lugar do traço: separa o cabeçalho do
        # conteúdo sem cortar a tela com uma linha cinza.
        shadow=t.SOMBRA_CARD,
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


def quadrado_de_categoria(icone: str | None, lado: int = 46) -> ft.Container:
    """Ícone da categoria em um quadrado tom sobre tom.

    A cor sai de `theme.cores_da_categoria`, então a mesma categoria tem o mesmo
    par (ícone, fundo) na grade da Home, no cartão e no detalhe.
    """
    cor_icone, cor_fundo = t.cores_da_categoria(icone)
    return ft.Container(
        content=t.icone_por_nome(icone or "category", int(lado * 0.48), cor_icone),
        width=lado,
        height=lado,
        bgcolor=cor_fundo,
        border_radius=t.RAIO_BOTAO,
        alignment=ft.Alignment.CENTER,
    )


def cartao_solicitacao(
    solicitacao: dict[str, Any], ao_clicar: Callable[[int], None]
) -> ft.Container:
    """Cartão de pedido de ajuda: urgência, distância e tempo de publicação.

    A hierarquia é a mesma em toda lista do app: quadrado da categoria, badges,
    título em bold, metadados em cinza e o chevron à direita — que é o que
    informa, sem texto, que o cartão inteiro abre uma tela.
    """
    badges: list[ft.Control] = [t.badge_urgencia(solicitacao.get("urgencia", "media"))]
    if solicitacao.get("emergencia"):
        badges.insert(0, t.badge_emergencia())
    badges.append(
        t.etiqueta(
            solicitacao.get("distancia_formatada", "--"),
            cor_texto=t.TEXTO_SECUNDARIO,
            cor_fundo=t.CINZA_CLARO,
            icone=t.ICONES["local"],
        )
    )

    # Pessoas e tempo em uma linha só, separados por ponto médio: dois
    # metadados curtos brigam menos assim do que como dois pares ícone+texto.
    pessoas = solicitacao.get("pessoas_beneficiadas", 1)
    partes = [f"{pessoas} pessoa{'s' if pessoas != 1 else ''}"]
    if solicitacao.get("tempo_publicacao"):
        partes.append(str(solicitacao["tempo_publicacao"]))

    conteudo = ft.Row(
        [
            quadrado_de_categoria(solicitacao.get("categoria_icone")),
            ft.Column(
                [
                    ft.Row(badges, spacing=6, wrap=True, run_spacing=4),
                    t.titulo_cartao(
                        solicitacao.get("titulo", ""),
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    t.meta(" · ".join(partes)),
                ],
                spacing=6,
                expand=True,
            ),
            ft.Icon(t.ICONES["detalhe"], size=20, color=t.TEXTO_INATIVO),
        ],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
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
    """Cartão de oferta: quem está doando, o quê e a que distância.

    Mesma estrutura do cartão de solicitação — quadrado, badges, título, meta —
    para que a lista de Explorar, que mistura os dois, se leia como uma só.
    Aqui o quadrado mostra o **tipo de ajuda** (item, entrega, retirada), que é a
    informação que distingue uma oferta da outra.
    """
    tipo = oferta.get("tipo_ajuda", "tenho_item")

    direita: list[ft.Control] = []
    if ao_clicar is not None:
        direita.append(ft.Icon(t.ICONES["detalhe"], size=20, color=t.TEXTO_INATIVO))

    partes = [p for p in (oferta.get("autor_nome"), oferta.get("tempo_publicacao")) if p]

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
                border_radius=t.RAIO_BOTAO,
                alignment=ft.Alignment.CENTER,
            ),
            ft.Column(
                [
                    ft.Row(
                        [
                            t.etiqueta(ROTULOS_TIPO_AJUDA.get(tipo, tipo)),
                            t.etiqueta(
                                oferta.get("distancia_formatada", "--"),
                                cor_texto=t.TEXTO_SECUNDARIO,
                                cor_fundo=t.CINZA_CLARO,
                                icone=t.ICONES["local"],
                            ),
                        ],
                        spacing=6,
                        wrap=True,
                        run_spacing=4,
                    ),
                    t.titulo_cartao(
                        oferta.get("titulo", ""),
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    t.meta(" · ".join(partes)),
                ],
                spacing=6,
                expand=True,
            ),
            *direita,
        ],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
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
            color=t.TEXTO_FORTE,
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
                            ft.Text("·", size=12, color=t.TEXTO_INATIVO),
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
            ft.Icon(t.ICONES["detalhe"], size=20, color=t.TEXTO_INATIVO),
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
                        color=t.TEXTO_FORTE,
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
    filhos: list[ft.Control] = [t.titulo_secao(titulo_texto)]
    if acao is not None:
        filhos.append(acao)
    return ft.Row(filhos, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
