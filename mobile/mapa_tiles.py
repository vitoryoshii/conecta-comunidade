"""
Projeção Web Mercator e grade de tiles do OpenStreetMap.

É o que permite desenhar um mapa **de verdade** — com ruas — sem WebView e sem
chave de API: as imagens de tile do OSM são baixadas pelo próprio `ft.Image`, e
estas funções dizem *quais* baixar e *onde* colocar cada uma, além de converter
lat/long em pixels dentro da área desenhada (que é como os pinos param no lugar
certo em cima das ruas).

O esquema é o "slippy map" padrão: no zoom `z` o mundo é uma grade de 2^z × 2^z
tiles de 256px. As fórmulas são as da própria especificação do OSM.

Uso dos tiles: a política do OpenStreetMap permite tráfego leve como este (uma
tela, poucos tiles, com cache do próprio cliente). Um app com muitos usuários
precisa de um provedor de tiles próprio — vale lembrar disso antes de publicar.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

LADO_DO_TILE = 256

URL_DO_TILE = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"

# Atribuição obrigatória pela licença dos dados do OpenStreetMap.
CREDITO = "© OpenStreetMap"

ZOOM_PADRAO = 13
ZOOM_MINIMO = 3
ZOOM_MAXIMO = 17

# O Mercator não representa os polos: a projeção é cortada nesta latitude, que é
# onde o mundo vira um quadrado.
LATITUDE_LIMITE = 85.05112878


@dataclass(frozen=True)
class Tile:
    """Uma imagem de tile já posicionada dentro da área do mapa."""

    z: int
    x: int
    y: int
    left: float
    top: float

    @property
    def url(self) -> str:
        """Endereço da imagem no servidor de tiles do OSM."""
        return URL_DO_TILE.format(z=self.z, x=self.x, y=self.y)


def projetar(latitude: float, longitude: float, zoom: int) -> tuple[float, float]:
    """Converte lat/long em pixels globais do mundo, naquele zoom."""
    latitude = max(-LATITUDE_LIMITE, min(LATITUDE_LIMITE, latitude))
    lado_do_mundo = LADO_DO_TILE * (2**zoom)

    x = (longitude + 180.0) / 360.0 * lado_do_mundo

    seno = math.sin(math.radians(latitude))
    y = (0.5 - math.log((1 + seno) / (1 - seno)) / (4 * math.pi)) * lado_do_mundo
    return x, y


def centro_dos_pontos(
    pontos: Sequence[tuple[float, float]], padrao: tuple[float, float]
) -> tuple[float, float]:
    """Centro do retângulo que contém todos os pontos (ou `padrao`, sem pontos)."""
    if not pontos:
        return padrao

    latitudes = [lat for lat, _ in pontos]
    longitudes = [lng for _, lng in pontos]
    return (
        (min(latitudes) + max(latitudes)) / 2,
        (min(longitudes) + max(longitudes)) / 2,
    )


def zoom_que_cobre(
    pontos: Sequence[tuple[float, float]],
    largura: int,
    altura: int,
    margem: int = 56,
) -> int:
    """Maior zoom em que todos os pontos cabem na área, com folga nas bordas.

    Com um ponto só (ou nenhum) não há o que enquadrar: vale o `ZOOM_PADRAO`, o
    zoom de bairro pedido para a tela.
    """
    if len(pontos) < 2:
        return ZOOM_PADRAO

    latitudes = [lat for lat, _ in pontos]
    longitudes = [lng for _, lng in pontos]
    util_x = max(1, largura - 2 * margem)
    util_y = max(1, altura - 2 * margem)

    for zoom in range(ZOOM_MAXIMO, ZOOM_MINIMO - 1, -1):
        x1, y1 = projetar(max(latitudes), min(longitudes), zoom)
        x2, y2 = projetar(min(latitudes), max(longitudes), zoom)
        if (x2 - x1) <= util_x and (y2 - y1) <= util_y:
            return zoom

    return ZOOM_MINIMO


def origem(
    centro: tuple[float, float], zoom: int, largura: int, altura: int
) -> tuple[float, float]:
    """Pixel global correspondente ao canto superior esquerdo da área."""
    x, y = projetar(centro[0], centro[1], zoom)
    return x - largura / 2, y - altura / 2


def grade(
    centro: tuple[float, float], zoom: int, largura: int, altura: int
) -> list[Tile]:
    """Tiles necessários para cobrir a área, já posicionados em pixels.

    Fora das bordas do mundo não existe tile: nessas colunas/linhas nada é
    pedido ao servidor, e o fundo da área aparece no lugar.
    """
    origem_x, origem_y = origem(centro, zoom, largura, altura)
    total = 2**zoom

    primeira_coluna = math.floor(origem_x / LADO_DO_TILE)
    ultima_coluna = math.floor((origem_x + largura) / LADO_DO_TILE)
    primeira_linha = math.floor(origem_y / LADO_DO_TILE)
    ultima_linha = math.floor((origem_y + altura) / LADO_DO_TILE)

    tiles: list[Tile] = []
    for x in range(primeira_coluna, ultima_coluna + 1):
        for y in range(primeira_linha, ultima_linha + 1):
            if not (0 <= y < total):
                continue
            # A longitude dá a volta no mundo; a latitude, não.
            tiles.append(
                Tile(
                    z=zoom,
                    x=x % total,
                    y=y,
                    left=x * LADO_DO_TILE - origem_x,
                    top=y * LADO_DO_TILE - origem_y,
                )
            )
    return tiles


def posicao_na_area(
    latitude: float,
    longitude: float,
    centro: tuple[float, float],
    zoom: int,
    largura: int,
    altura: int,
) -> tuple[float, float]:
    """Posição do ponto em pixels **dentro** da área desenhada."""
    origem_x, origem_y = origem(centro, zoom, largura, altura)
    x, y = projetar(latitude, longitude, zoom)
    return x - origem_x, y - origem_y


def coordenadas(pontos: Iterable[dict]) -> list[tuple[float, float]]:
    """Extrai os pares (lat, long) dos pontos vindos da API."""
    return [
        (float(p["latitude"]), float(p["longitude"]))
        for p in pontos
        if p.get("latitude") is not None and p.get("longitude") is not None
    ]
