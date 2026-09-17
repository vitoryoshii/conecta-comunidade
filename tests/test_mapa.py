"""
Testes do mapa real: projeção Web Mercator, grade de tiles e página Leaflet.

A matemática vive separada da tela justamente para poder ser conferida aqui: se
a projeção errar, o pino aparece na rua errada, e isso não aparece em nenhum
teste de renderização.
"""

import json
import math
import re

from mobile import mapa_leaflet, mapa_tiles

# Praça da Sé, marco zero de São Paulo.
SE = (-23.5505, -46.6333)

LARGURA = 380
ALTURA = 300


# --------------------------------------------------------------------------- #
# Projeção
# --------------------------------------------------------------------------- #
def test_projecao_cobre_o_mundo_inteiro() -> None:
    """Os extremos do mundo caem nos cantos da grade de pixels."""
    lado_do_mundo = mapa_tiles.LADO_DO_TILE * 2**3

    esquerda, _ = mapa_tiles.projetar(0, -180, 3)
    direita, _ = mapa_tiles.projetar(0, 180, 3)
    _, meio = mapa_tiles.projetar(0, 0, 3)

    assert esquerda == 0
    assert direita == lado_do_mundo
    # O equador divide o mundo ao meio na vertical.
    assert meio == lado_do_mundo / 2


def test_projecao_respeita_o_limite_do_mercator() -> None:
    """Além de ±85,05° a projeção satura, em vez de estourar para o infinito."""
    _, topo = mapa_tiles.projetar(89.9, 0, 5)
    _, limite = mapa_tiles.projetar(mapa_tiles.LATITUDE_LIMITE, 0, 5)

    assert topo == limite
    assert math.isfinite(topo)


def test_projecao_bate_com_o_tile_conhecido_de_sao_paulo() -> None:
    """Sé no zoom 13 cai no tile 3034/4647 — o mesmo que o OSM serve.

    Valor conferido pela fórmula oficial do "slippy map": é o teste que pega uma
    inversão de sinal ou um radiano trocado por grau.
    """
    x, y = mapa_tiles.projetar(*SE, 13)

    assert int(x // mapa_tiles.LADO_DO_TILE) == 3034
    assert int(y // mapa_tiles.LADO_DO_TILE) == 4647


def test_norte_fica_acima_e_leste_a_direita() -> None:
    """Orientação do mapa: latitude maior é mais para cima, no eixo invertido."""
    sul, norte = (-24.0, -46.6), (-23.0, -46.6)
    oeste, leste = (-23.5, -47.0), (-23.5, -46.0)

    _, y_sul = mapa_tiles.projetar(*sul, 10)
    _, y_norte = mapa_tiles.projetar(*norte, 10)
    x_oeste, _ = mapa_tiles.projetar(*oeste, 10)
    x_leste, _ = mapa_tiles.projetar(*leste, 10)

    assert y_norte < y_sul
    assert x_oeste < x_leste


# --------------------------------------------------------------------------- #
# Enquadramento e grade
# --------------------------------------------------------------------------- #
def test_zoom_enquadra_todos_os_pontos() -> None:
    """O zoom escolhido faz todos os pontos caberem na área desenhada."""
    pontos = [(-23.5545, -46.6896), (-23.6600, -46.7700), (-23.5460, -46.6360)]

    zoom = mapa_tiles.zoom_que_cobre(pontos, LARGURA, ALTURA)
    centro = mapa_tiles.centro_dos_pontos(pontos, SE)

    for latitude, longitude in pontos:
        x, y = mapa_tiles.posicao_na_area(
            latitude, longitude, centro, zoom, LARGURA, ALTURA
        )
        assert 0 <= x <= LARGURA, "ponto fora da área na horizontal"
        assert 0 <= y <= ALTURA, "ponto fora da área na vertical"


def test_zoom_padrao_quando_nao_ha_o_que_enquadrar() -> None:
    """Sem pontos, ou com um só, o mapa abre no zoom de bairro."""
    assert mapa_tiles.zoom_que_cobre([], LARGURA, ALTURA) == mapa_tiles.ZOOM_PADRAO
    assert mapa_tiles.zoom_que_cobre([SE], LARGURA, ALTURA) == mapa_tiles.ZOOM_PADRAO


def test_grade_cobre_a_area_sem_buraco() -> None:
    """Os tiles pedidos cobrem toda a área, e nenhum é pedido à toa."""
    tiles = mapa_tiles.grade(SE, 13, LARGURA, ALTURA)

    assert tiles, "a área precisa de pelo menos um tile"
    # Nenhum tile começa depois do fim da área nem termina antes do começo.
    for tile in tiles:
        assert tile.left + mapa_tiles.LADO_DO_TILE > 0
        assert tile.top + mapa_tiles.LADO_DO_TILE > 0
        assert tile.left < LARGURA
        assert tile.top < ALTURA

    # Cobertura: o canto superior esquerdo e o inferior direito têm tile.
    def cobre(px: float, py: float) -> bool:
        return any(
            tile.left <= px < tile.left + mapa_tiles.LADO_DO_TILE
            and tile.top <= py < tile.top + mapa_tiles.LADO_DO_TILE
            for tile in tiles
        )

    assert cobre(0, 0)
    assert cobre(LARGURA - 1, ALTURA - 1)


def test_grade_so_pede_tiles_que_existem() -> None:
    """Perto do polo e da antimeridiana, a grade não inventa tile."""
    tiles = mapa_tiles.grade((84.0, 179.5), 4, LARGURA, ALTURA)
    total = 2**4

    for tile in tiles:
        assert 0 <= tile.x < total
        assert 0 <= tile.y < total
        assert tile.url.startswith("https://tile.openstreetmap.org/4/")


def test_centro_dos_pontos_usa_o_padrao_quando_nao_ha_pontos() -> None:
    """Sem ponto algum, o mapa abre onde o app mandar (usuário ou centro fixo)."""
    assert mapa_tiles.centro_dos_pontos([], SE) == SE


def test_coordenadas_ignora_ponto_sem_localizacao() -> None:
    """Ponto sem lat/long não entra no enquadramento."""
    pontos = [
        {"latitude": -23.5, "longitude": -46.6},
        {"latitude": None, "longitude": None},
        {"titulo": "sem coordenadas"},
    ]

    assert mapa_tiles.coordenadas(pontos) == [(-23.5, -46.6)]


# --------------------------------------------------------------------------- #
# Página Leaflet
# --------------------------------------------------------------------------- #
def test_html_do_leaflet_leva_os_pontos_e_as_cores() -> None:
    """A página abre no centro pedido e conhece cada ponto e sua cor."""
    pontos = [
        {
            "id": 7,
            "tipo": "ajuda",
            "titulo": "Cestas básicas",
            "latitude": -23.55,
            "longitude": -46.63,
            "emergencia": True,
            "distancia_formatada": "1,2 km",
        },
        {
            "id": 9,
            "tipo": "ong",
            "titulo": "Instituto Semear",
            "latitude": -23.54,
            "longitude": -46.64,
        },
    ]

    html = mapa_leaflet.montar_html(pontos, SE, 13)

    assert "tile.openstreetmap.org" in html
    assert "OpenStreetMap" in html, "a atribuição é exigida pela licença"
    assert ".setView([-23.5505, -46.6333], 13)" in html
    # Sem o fade, os tiles aparecem assim que baixam — inclusive com a janela
    # em segundo plano, onde a animação do Leaflet não roda.
    assert "fadeAnimation: false" in html

    dados = json.loads(re.search(r"var pontos = (\[.*?\]);", html, re.S).group(1))
    assert [p["id"] for p in dados] == [7, 9]
    assert dados[0]["emergencia"] is True
    assert dados[1]["rotulo"] == "ONG"

    # As quatro cores do app chegam ao JavaScript.
    assert json.loads(re.search(r"var cores = (\{.*?\});", html, re.S).group(1)) == {
        "ajuda": "#E23B3B",
        "oferecendo": "#1FA96C",
        "ong": "#0E2A47",
        "ponto_retirada": "#F5A623",
    }


def test_html_do_leaflet_nao_deixa_o_titulo_virar_marcacao() -> None:
    """Título com aspas e tags vira texto, e não script dentro da página."""
    pontos = [
        {
            "id": 1,
            "tipo": "ajuda",
            "titulo": '</script><img src=x onerror="alert(1)">',
            "latitude": -23.5,
            "longitude": -46.6,
        }
    ]

    html = mapa_leaflet.montar_html(pontos, SE)

    # O que importa não é a palavra "onerror" aparecer no arquivo — ela é só
    # texto dentro de uma string —, e sim que nenhum `<` do dado chegue cru ao
    # HTML: sem isso, o `</script>` do título fecharia a tag e o resto viraria
    # marcação de verdade.
    assert "<img" not in html, "o título não pode sair cru no HTML"
    assert html.count("</script>") == 2, "só as duas tags do próprio arquivo"
    assert "\\u003c" in html, "os sinais de menor saem escapados"

    # O título continua íntegro: o JavaScript o lê de volta como texto, e o
    # popup o insere com `textContent`, que nunca interpreta marcação.
    dados = json.loads(re.search(r"var pontos = (\[.*?\]);", html, re.S).group(1))
    assert dados[0]["titulo"] == '</script><img src=x onerror="alert(1)">'
    assert "textContent" in html


def test_html_sem_pontos_ainda_abre() -> None:
    """Com os filtros zerados, a página abre no centro e avisa que está vazia."""
    html = mapa_leaflet.montar_html([], SE)

    assert "var pontos = []" in html
    assert "Nenhum ponto com os filtros atuais" in html


def test_url_do_mapa_gera_arquivo_local_legivel(tmp_path) -> None:
    """A URL entregue ao navegador aponta para um arquivo que existe."""
    from pathlib import Path
    from urllib.parse import urlparse
    from urllib.request import url2pathname

    url = mapa_leaflet.url_do_mapa([], SE)

    assert url.startswith("file://")
    caminho = Path(url2pathname(urlparse(url).path))
    assert caminho.is_file()
    assert "leaflet" in caminho.read_text(encoding="utf-8").lower()
    caminho.unlink()
