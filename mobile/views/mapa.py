"""
Tela 9 — Mapa.

O pacote base do Flet 0.86 não traz o controle `ft.Map` (ele vive na extensão
`flet-map`, que exige build nativo). Para o app funcionar em qualquer máquina
sem passo extra de instalação, desenhamos aqui um **mapa esquemático**: uma
tela de coordenadas onde cada pin é posicionado proporcionalmente à sua
latitude/longitude, com a mesma paleta e os mesmos filtros por tipo previstos
no projeto. A lista logo abaixo mostra os mesmos pontos em detalhe.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from mobile import theme as t

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

TIPOS = ["ajuda", "oferecendo", "ong", "ponto_retirada"]

# Dimensões da área de desenho do mapa esquemático.
LARGURA_MAPA = 330
ALTURA_MAPA = 250
MARGEM = 26


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
                        t.etiqueta(f"{len(pontos)} ponto(s)", icone=ft.Icons.PLACE_OUTLINED),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                t.subtitulo("Toque em um pino para ver os detalhes."),
                _mapa_esquematico(app, pontos),
                _painel_de_filtros(ativos, totais, alternar),
                ft.Text(
                    "Pontos listados",
                    size=15,
                    weight=ft.FontWeight.BOLD,
                    color=t.AZUL_INSTITUCIONAL,
                ),
                _lista_de_pontos(app, pontos),
                ft.Container(height=10),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        padding=ft.Padding.symmetric(horizontal=16, vertical=14),
        expand=True,
        bgcolor=t.FUNDO_CLARO,
    )


def _mapa_esquematico(app: App, pontos: list[dict[str, Any]]) -> ft.Control:
    """Desenha os pins posicionados por lat/long dentro de uma área fixa.

    A projeção é linear: encontramos os extremos das coordenadas e mapeamos
    cada ponto para a área de desenho. Não é uma projeção cartográfica de
    verdade, mas preserva a posição relativa entre os pontos.
    """
    grade: list[ft.Control] = [
        # Linhas de grade, apenas para dar leitura de "mapa" à área.
        ft.Container(
            left=0,
            top=y,
            width=LARGURA_MAPA,
            height=1,
            bgcolor="#DDE7E1",
        )
        for y in range(42, ALTURA_MAPA, 52)
    ]
    grade += [
        ft.Container(left=x, top=0, width=1, height=ALTURA_MAPA, bgcolor="#DDE7E1")
        for x in range(55, LARGURA_MAPA, 55)
    ]

    if not pontos:
        grade.append(
            ft.Container(
                content=ft.Text(
                    "Nenhum ponto com os filtros atuais.",
                    size=12,
                    color=t.TEXTO_SECUNDARIO,
                ),
                left=0,
                top=ALTURA_MAPA / 2 - 10,
                width=LARGURA_MAPA,
                alignment=ft.Alignment.CENTER,
            )
        )
    else:
        latitudes = [p["latitude"] for p in pontos]
        longitudes = [p["longitude"] for p in pontos]
        lat_min, lat_max = min(latitudes), max(latitudes)
        lon_min, lon_max = min(longitudes), max(longitudes)

        def escalar(valor: float, minimo: float, maximo: float, tamanho: int) -> float:
            """Mapeia um valor do intervalo geográfico para pixels."""
            if maximo - minimo < 1e-9:  # todos os pontos no mesmo lugar
                return tamanho / 2
            proporcao = (valor - minimo) / (maximo - minimo)
            return MARGEM + proporcao * (tamanho - 2 * MARGEM)

        for ponto in pontos:
            # Latitude cresce para o norte, mas o eixo Y da tela cresce para
            # baixo — por isso a inversão.
            x = escalar(ponto["longitude"], lon_min, lon_max, LARGURA_MAPA)
            y = ALTURA_MAPA - escalar(ponto["latitude"], lat_min, lat_max, ALTURA_MAPA)
            grade.append(_pino(app, ponto, x, y))

    # A área tem tamanho fixo e recorte rígido: as posições dos pinos são
    # calculadas em pixels, então o container precisa medir exatamente o mesmo
    # que o Stack — do contrário um pino pode vazar pela borda.
    area = ft.Container(
        content=ft.Stack(grade, width=LARGURA_MAPA, height=ALTURA_MAPA),
        width=LARGURA_MAPA,
        height=ALTURA_MAPA,
        bgcolor="#E9F1EC",
        border_radius=t.RAIO,
        border=ft.Border.all(1, t.BORDA),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        padding=0,
    )
    # Em telas estreitas a Row rola na horizontal; em telas largas, centraliza.
    return ft.Row([area], alignment=ft.MainAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)


def _pino(app: App, ponto: dict[str, Any], x: float, y: float) -> ft.Container:
    """Um marcador clicável do mapa."""
    tipo = ponto.get("tipo", "ajuda")
    cor = t.URGENCIA if ponto.get("emergencia") else t.CORES_MAPA.get(tipo, t.VERDE_PRIMARIO)
    tamanho = 34 if ponto.get("emergencia") else 28

    return ft.Container(
        content=ft.Icon(t.ICONES_MAPA.get(tipo, ft.Icons.PLACE), size=tamanho / 2, color=t.BRANCO),
        width=tamanho,
        height=tamanho,
        bgcolor=cor,
        border_radius=tamanho / 2,
        border=ft.Border.all(2, t.BRANCO),
        alignment=ft.Alignment.CENTER,
        left=max(0, min(x - tamanho / 2, LARGURA_MAPA - tamanho)),
        top=max(0, min(y - tamanho / 2, ALTURA_MAPA - tamanho)),
        tooltip=f"{ponto.get('titulo', '')} · {ponto.get('distancia_formatada', '--')}",
        on_click=lambda _: _abrir(app, ponto),
        shadow=ft.BoxShadow(blur_radius=6, color="#33000000", offset=ft.Offset(0, 2)),
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
                            bgcolor=cor if ligado else t.BORDA,
                            border_radius=12,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Text(
                            t.ROTULOS_MAPA[tipo],
                            size=12,
                            color=t.AZUL_INSTITUCIONAL if ligado else t.TEXTO_SECUNDARIO,
                            weight=ft.FontWeight.W_600 if ligado else ft.FontWeight.NORMAL,
                            expand=True,
                        ),
                        ft.Text(str(totais.get(tipo, 0)), size=12, color=t.TEXTO_SECUNDARIO),
                        ft.Icon(
                            ft.Icons.TOGGLE_ON if ligado else ft.Icons.TOGGLE_OFF,
                            size=26,
                            color=cor if ligado else t.BORDA,
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
                ft.Text(
                    "Filtrar por tipo",
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=t.AZUL_INSTITUCIONAL,
                ),
                *linhas,
            ],
            spacing=2,
        ),
        padding=12,
    )


def _lista_de_pontos(app: App, pontos: list[dict[str, Any]]) -> ft.Control:
    """Lista textual dos pins, com coordenadas e distância."""
    if not pontos:
        return t.area_vazia("Nenhum ponto para exibir.", ft.Icons.LOCATION_OFF)

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
                                        ft.Text(
                                            ponto.get("titulo", ""),
                                            size=13,
                                            weight=ft.FontWeight.W_600,
                                            color=t.AZUL_INSTITUCIONAL,
                                            max_lines=1,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                            expand=True,
                                        ),
                                        *([t.selo_verificada()] if ponto.get("verificada") else []),
                                    ],
                                    spacing=4,
                                ),
                                ft.Text(
                                    f"{ponto.get('subtitulo', '')} · "
                                    f"{ponto.get('distancia_formatada', '--')}",
                                    size=11,
                                    color=t.TEXTO_SECUNDARIO,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Text(
                                    f"{ponto.get('latitude', 0):.4f}, {ponto.get('longitude', 0):.4f}",
                                    size=10,
                                    color=t.BORDA,
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=t.BORDA),
                    ],
                    spacing=10,
                ),
                padding=12,
                on_click=lambda _, p=ponto: _abrir(app, p),
            )
        )

    return ft.Column(linhas, spacing=8)


def _abrir(app: App, ponto: dict[str, Any]) -> None:
    """Leva o usuário à tela correspondente ao tipo do pin."""
    tipo = ponto.get("tipo")
    if tipo == "ajuda":
        app.navegar("detalhe_solicitacao", id=ponto["id"])
    elif tipo == "ong":
        app.navegar("perfil_ong", id=ponto["id"])
    else:
        app.aviso(f"{ponto.get('titulo', '')} · {ponto.get('distancia_formatada', '--')} de você")
