"""
Tela 9 — Mapa.

Mapa **real**: as imagens de tile do OpenStreetMap são baixadas pelo próprio
`ft.Image` e montadas em um `Stack`, com os pinos posicionados por cima pela
mesma projeção Web Mercator (`mobile/mapa_tiles.py`). Ou seja, ruas de verdade,
sem chave de API, sem dependência nova e sem WebView.

Sobre o WebView: o `ft.WebView` **não existe** no pacote `flet` 0.86 — virou o
pacote separado `flet-webview`, cujo plugin Flutter não suporta Windows
desktop, que é onde o app é demonstrado. Por isso o mapa embutido é o de tiles,
e o mapa interativo (zoom, arrasto, popups) é uma página Leaflet aberta no
navegador pelo botão "Abrir mapa interativo" (`mobile/mapa_leaflet.py`).

A área nunca cai no retângulo vazio: sem internet, o `error_content` de cada
tile mostra a superfície verde-clara, e os pinos continuam nas posições certas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from mobile import mapa_leaflet, mapa_tiles
from mobile import theme as t
from mobile.components.fab import ESPACO_PARA_O_FAB

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

TIPOS = ["ajuda", "oferecendo", "ong", "ponto_retirada"]

# Dimensões da área do mapa. São fixas de propósito: as posições dos tiles e
# dos pinos são calculadas em pixels a partir delas.
LARGURA_MAPA = 380
ALTURA_MAPA = 300
TAMANHO_PIN = 30
TAMANHO_PIN_EMERGENCIA = 38

# Centro usado quando não há nem usuário localizado nem pontos: o centro de São
# Paulo, que é a região da demonstração.
CENTRO_PADRAO = (-23.5505, -46.6333)


def construir(app: App) -> ft.Control:
    """Monta o mapa esquemático, o painel de filtros e a lista de pontos."""
    parametros = app.state.rota_atual.parametros
    # Por padrão, todos os tipos de pin ficam visíveis.
    ativos: list[str] = list(parametros.get("tipos", TIPOS))

    resposta = app.executar(
        lambda: app.api.pontos_do_mapa(tipos=ativos, **app.coordenadas())
    ) or {"pontos": [], "total_por_tipo": {}}

    pontos: list[dict[str, Any]] = resposta.get("pontos", [])
    totais: dict[str, int] = resposta.get("total_por_tipo", {})

    def alternar(tipo: str) -> None:
        """Liga/desliga um tipo de pin no painel de filtros."""
        novos = [x for x in ativos if x != tipo] if tipo in ativos else [*ativos, tipo]
        # Nunca deixamos a lista vazia: sem tipo algum, o mapa não diria nada.
        app.substituir("mapa", tipos=novos or TIPOS)

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        t.titulo("Mapa", 22),
                        t.etiqueta(
                            f"{len(pontos)} ponto{'s' if len(pontos) != 1 else ''}",
                            icone=t.ICONES["local"],
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                t.subtitulo("Toque em um pino para abrir os detalhes do ponto."),
                _mapa(app, pontos),
                _botao_interativo(app, pontos),
                _painel_de_filtros(ativos, totais, alternar),
                t.titulo_secao("Pontos listados"),
                _lista_de_pontos(app, pontos),
                # Folga para o último ponto não terminar embaixo do FAB.
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


def _botao_interativo(app: App, pontos: list[dict[str, Any]]) -> ft.Container:
    """Abre a versão com zoom e arrasto (Leaflet) no navegador.

    O mapa da tela é uma imagem: mostra onde as coisas estão, mas não se mexe.
    Quem precisa procurar um endereço abre esta versão, que leva os mesmos
    pontos, com os mesmos filtros já aplicados.
    """

    def abrir(_: ft.ControlEvent) -> None:
        centro, zoom = _centro_e_zoom(app, pontos)
        try:
            endereco = mapa_leaflet.url_do_mapa(pontos, centro, zoom)
        except OSError:
            app.aviso("Não foi possível preparar o mapa interativo.", erro=True)
            return
        app.page.launch_url(endereco)
        app.aviso("Mapa interativo aberto no navegador.")

    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.OPEN_IN_NEW_ROUNDED, size=16, color=t.VERDE_PRIMARIO),
                ft.Text(
                    "Abrir mapa interativo",
                    size=12.5,
                    weight=ft.FontWeight.W_600,
                    color=t.VERDE_PRIMARIO,
                ),
            ],
            spacing=6,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        on_click=abrir,
        padding=ft.Padding.symmetric(horizontal=12, vertical=10),
        bgcolor=t.BRANCO,
        border_radius=t.RAIO_BOTAO,
        shadow=t.SOMBRA_CARD,
        ink=True,
        tooltip="Mapa com zoom e arrasto, no navegador",
    )


def _centro_e_zoom(
    app: App, pontos: list[dict[str, Any]]
) -> tuple[tuple[float, float], int]:
    """Onde o mapa abre e em que zoom.

    Com pontos, enquadramos todos; com um só (ou nenhum), centramos no usuário
    e usamos o zoom de bairro. Sem usuário localizado, resta o centro padrão.
    """
    coordenadas = mapa_tiles.coordenadas(pontos)
    do_usuario = app.coordenadas()
    padrao = (
        (do_usuario["lat"], do_usuario["long"])
        if do_usuario
        else CENTRO_PADRAO
    )

    centro = mapa_tiles.centro_dos_pontos(coordenadas, padrao)
    zoom = mapa_tiles.zoom_que_cobre(coordenadas, LARGURA_MAPA, ALTURA_MAPA)
    return centro, zoom


def _tiles(centro: tuple[float, float], zoom: int) -> list[ft.Control]:
    """Imagens de tile do OSM que cobrem a área, já posicionadas."""
    return [
        ft.Image(
            src=tile.url,
            width=mapa_tiles.LADO_DO_TILE,
            height=mapa_tiles.LADO_DO_TILE,
            fit=ft.BoxFit.COVER,
            left=tile.left,
            top=tile.top,
            # Sem internet (ou com o tile indisponível), o buraco fica com a
            # cor da superfície em vez de um ícone de imagem quebrada.
            error_content=ft.Container(
                width=mapa_tiles.LADO_DO_TILE,
                height=mapa_tiles.LADO_DO_TILE,
                bgcolor="#E8F2EC",
            ),
        )
        for tile in mapa_tiles.grade(centro, zoom, LARGURA_MAPA, ALTURA_MAPA)
    ]


def _credito() -> ft.Container:
    """Atribuição ao OpenStreetMap, exigida pela licença dos dados."""
    return ft.Container(
        content=ft.Text(mapa_tiles.CREDITO, size=9, color=t.TEXTO_FORTE),
        padding=ft.Padding.symmetric(horizontal=6, vertical=2),
        bgcolor="#CCFFFFFF",
        border_radius=6,
        right=6,
        bottom=6,
    )


def _aviso_sobre_o_mapa(texto: str) -> ft.Container:
    """Mensagem centralizada sobre o mapa (sem pontos, sem coordenadas)."""
    return ft.Container(
        content=ft.Text(
            texto,
            size=12,
            color=t.TEXTO_FORTE,
            text_align=ft.TextAlign.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=14, vertical=10),
        bgcolor="#F2FFFFFF",
        border_radius=t.RAIO_BOTAO,
        shadow=t.SOMBRA_CARD,
        left=24,
        top=ALTURA_MAPA / 2 - 22,
        width=LARGURA_MAPA - 48,
        alignment=ft.Alignment.CENTER,
    )


def _mapa(app: App, pontos: list[dict[str, Any]]) -> ft.Control:
    """Mapa do OSM com os pinos dos pontos por cima."""
    centro, zoom = _centro_e_zoom(app, pontos)
    camadas: list[ft.Control] = _tiles(centro, zoom)

    com_coordenadas = [
        ponto
        for ponto in pontos
        if isinstance(ponto.get("latitude"), int | float)
        and isinstance(ponto.get("longitude"), int | float)
    ]

    for ponto in com_coordenadas:
        x, y = mapa_tiles.posicao_na_area(
            ponto["latitude"], ponto["longitude"], centro, zoom, LARGURA_MAPA, ALTURA_MAPA
        )
        camadas.append(_pino(app, ponto, x, y))

    if not pontos:
        camadas.append(_aviso_sobre_o_mapa("Nenhum ponto com os filtros atuais."))
    elif not com_coordenadas:
        camadas.append(
            _aviso_sobre_o_mapa("Os pontos retornados não têm coordenadas válidas.")
        )

    camadas.append(_credito())
    return _area_do_mapa(camadas)


def _area_do_mapa(camadas: list[ft.Control]) -> ft.Control:
    """Superfície fixa do mapa: tiles, pinos e crédito, recortados no cartão.

    O tamanho é fixo e o recorte é rígido porque as posições dos tiles e dos
    pinos são calculadas em pixels a partir dele — um container de outra medida
    deslocaria tudo.
    """
    area = ft.Container(
        content=ft.Stack(
            list(camadas),
            width=LARGURA_MAPA,
            height=ALTURA_MAPA,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        ),
        width=LARGURA_MAPA,
        height=ALTURA_MAPA,
        # Cor da superfície enquanto os tiles carregam (e onde eles falharem).
        bgcolor="#E8F2EC",
        border_radius=t.RAIO_CARD,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        padding=0,
        shadow=t.SOMBRA_CARD,
    )
    # Em telas estreitas a Row rola na horizontal; em telas largas, centraliza.
    return ft.Row([area], alignment=ft.MainAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)


def _pino(app: App, ponto: dict[str, Any], x: float, y: float) -> ft.Container:
    """Um marcador clicável do mapa."""
    tipo = ponto.get("tipo", "ajuda")
    cor = t.URGENCIA if ponto.get("emergencia") else t.CORES_MAPA.get(tipo, t.VERDE_PRIMARIO)
    tamanho = TAMANHO_PIN_EMERGENCIA if ponto.get("emergencia") else TAMANHO_PIN

    return ft.Container(
        content=ft.Icon(t.ICONES_MAPA.get(tipo, t.ICONES["local"]), size=tamanho / 2, color=t.BRANCO),
        width=tamanho,
        height=tamanho,
        bgcolor=cor,
        border_radius=tamanho / 2,
        border=ft.Border.all(2, t.BRANCO),
        alignment=ft.Alignment.CENTER,
        left=max(0, min(x - tamanho / 2, LARGURA_MAPA - tamanho)),
        top=max(0, min(y - tamanho / 2, ALTURA_MAPA - tamanho)),
        tooltip=f"{ponto.get('titulo', '')} · {ponto.get('distancia_formatada', '--')}",
        on_click=lambda _: _abrir_detalhe(app, ponto),
        shadow=t.SOMBRA_CARD,
        ink=True,
    )


def _painel_de_filtros(
    ativos: list[str], totais: dict[str, int], alternar
) -> ft.Container:
    """Toggles por tipo de ponto, com a contagem de cada um."""
    linhas: list[ft.Control] = []
    for tipo in TIPOS:
        ligado = tipo in ativos
        cor = t.CORES_MAPA[tipo]
        linhas.append(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            content=ft.Icon(t.ICONES_MAPA[tipo], size=13, color=t.BRANCO),
                            width=24,
                            height=24,
                            bgcolor=cor if ligado else t.TEXTO_INATIVO,
                            border_radius=12,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Text(
                            t.ROTULOS_MAPA[tipo],
                            size=12,
                            color=t.TEXTO_FORTE if ligado else t.TEXTO_SECUNDARIO,
                            weight=ft.FontWeight.W_600 if ligado else ft.FontWeight.NORMAL,
                            expand=True,
                        ),
                        ft.Text(str(totais.get(tipo, 0)), size=12, color=t.TEXTO_SECUNDARIO),
                        ft.Icon(
                            ft.Icons.TOGGLE_ON_ROUNDED if ligado else ft.Icons.TOGGLE_OFF_ROUNDED,
                            size=28,
                            color=cor if ligado else t.TEXTO_INATIVO,
                        ),
                    ],
                    spacing=10,
                ),
                padding=ft.Padding.symmetric(vertical=6, horizontal=4),
                on_click=lambda _, x=tipo: alternar(x),
            )
        )

    return t.cartao(
        ft.Column(
            [
                t.titulo("Filtrar por tipo", 13),
                *linhas,
            ],
            spacing=2,
        ),
        padding=12,
    )


def _lista_de_pontos(app: App, pontos: list[dict[str, Any]]) -> ft.Control:
    """Lista textual dos pins, com coordenadas e distância."""
    if not pontos:
        return t.area_vazia("Nenhum ponto para exibir.", ft.Icons.LOCATION_OFF_OUTLINED)

    linhas: list[ft.Control] = []
    for ponto in pontos:
        tipo = ponto.get("tipo", "ajuda")
        cor = t.CORES_MAPA.get(tipo, t.VERDE_PRIMARIO)
        linhas.append(
            t.cartao(
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Icon(t.ICONES_MAPA[tipo], size=16, color=t.BRANCO),
                            width=34,
                            height=34,
                            bgcolor=t.URGENCIA if ponto.get("emergencia") else cor,
                            border_radius=17,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        t.titulo_cartao(
                                            ponto.get("titulo", ""),
                                            max_lines=1,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                            expand=True,
                                        ),
                                        *([t.selo_verificada()] if ponto.get("verificada") else []),
                                    ],
                                    spacing=4,
                                ),
                                t.meta(
                                    f"{ponto.get('subtitulo', '')} · "
                                    f"{ponto.get('distancia_formatada', '--')}",
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ],
                            spacing=3,
                            expand=True,
                        ),
                        ft.Icon(t.ICONES["detalhe"], size=20, color=t.TEXTO_INATIVO),
                    ],
                    spacing=10,
                ),
                padding=12,
                on_click=lambda _, p=ponto: _abrir_detalhe(app, p),
            )
        )

    return ft.Column(linhas, spacing=10)


def _abrir_detalhe(app: App, ponto: dict[str, Any]) -> None:
    """Abre um bottom sheet com os detalhes do pin tocado."""
    tipo = ponto.get("tipo")
    cor = t.CORES_MAPA.get(tipo, t.VERDE_PRIMARIO)

    acoes: list[ft.Control] = [
        t.botao_secundario("Fechar", lambda _: app.page.pop_dialog(), largura=130)
    ]
    if tipo == "ajuda":
        acoes.insert(
            0,
            t.botao_primario(
                "Ver pedido",
                lambda _: _fechar_e_navegar(app, "detalhe_solicitacao", id=ponto["id"]),
                t.ICONES["avancar"],
                150,
            ),
        )
    elif tipo == "ong":
        acoes.insert(
            0,
            t.botao_primario(
                "Ver ONG",
                lambda _: _fechar_e_navegar(app, "perfil_ong", id=ponto["id"]),
                t.ICONES["avancar"],
                150,
            ),
        )

    conteudo = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Icon(t.ICONES_MAPA.get(tipo, t.ICONES["local"]), color=t.BRANCO),
                            width=44,
                            height=44,
                            bgcolor=t.URGENCIA if ponto.get("emergencia") else cor,
                            border_radius=22,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        t.etiqueta(
                                            t.ROTULOS_MAPA.get(tipo, "Ponto"),
                                            cor_texto=t.BRANCO,
                                            cor_fundo=cor,
                                        ),
                                        *(
                                            [t.badge_emergencia()]
                                            if ponto.get("emergencia")
                                            else []
                                        ),
                                    ],
                                    spacing=6,
                                    wrap=True,
                                ),
                                t.titulo(ponto.get("titulo", ""), 18),
                            ],
                            spacing=6,
                            expand=True,
                        ),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                ft.Text(ponto.get("subtitulo", ""), size=13, color=t.TEXTO_SECUNDARIO),
                ft.Row(
                    [
                        _metrica_detalhe(
                            t.ICONES["local"],
                            ponto.get("distancia_formatada", "--"),
                            "distância",
                        ),
                        _metrica_detalhe(
                            t.ICONES["localizar"],
                            f"{ponto.get('latitude', 0):.4f}, {ponto.get('longitude', 0):.4f}",
                            "coordenadas",
                        ),
                    ],
                    spacing=10,
                    wrap=True,
                ),
                ft.Row(acoes, spacing=10, alignment=ft.MainAxisAlignment.END, wrap=True),
            ],
            spacing=14,
            tight=True,
        ),
        padding=20,
        bgcolor=t.BRANCO,
    )

    app.page.show_dialog(
        ft.BottomSheet(
            conteudo,
            bgcolor=t.BRANCO,
            dismissible=True,
            draggable=True,
            show_drag_handle=True,
            scrollable=True,
            shape=ft.RoundedRectangleBorder(radius=22),
        )
    )


def _metrica_detalhe(icone: ft.IconData, valor: str, rotulo: str) -> ft.Container:
    """Métrica compacta usada no detalhe do pin."""
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(icone, size=16, color=t.VERDE_PRIMARIO),
                ft.Column(
                    [
                        ft.Text(valor, size=13, color=t.TEXTO_FORTE, weight=ft.FontWeight.W_600),
                        ft.Text(rotulo, size=10, color=t.TEXTO_SECUNDARIO),
                    ],
                    spacing=0,
                ),
            ],
            spacing=8,
            tight=True,
        ),
        padding=ft.Padding.symmetric(horizontal=12, vertical=9),
        bgcolor=t.CINZA_CLARO,
        border_radius=t.RAIO_BOTAO,
    )


def _fechar_e_navegar(app: App, rota: str, **parametros: Any) -> None:
    """Fecha o bottom sheet antes de abrir uma tela de detalhe."""
    app.page.pop_dialog()
    app.navegar(rota, **parametros)
