"""
Serviço de geolocalização.

Responsável por calcular a distância entre o usuário logado e cada solicitação,
oferta ou ONG. Usamos a fórmula de haversine (distância de grande círculo)
através do `geopy`, que já trata o raio médio da Terra e retorna quilômetros.
"""

from geopy.distance import great_circle

# Coordenada "nula": quando um registro não tem localização informada, o
# cálculo de distância não faz sentido e devolvemos `None`.
_SEM_COORDENADA = (0.0, 0.0)


def coordenada_valida(latitude: float | None, longitude: float | None) -> bool:
    """Verifica se o par lat/long é utilizável em um cálculo de distância."""
    if latitude is None or longitude is None:
        return False
    if (latitude, longitude) == _SEM_COORDENADA:
        return False
    return -90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0


def calcular_distancia_km(
    origem_lat: float | None,
    origem_lon: float | None,
    destino_lat: float | None,
    destino_lon: float | None,
) -> float | None:
    """Distância em quilômetros entre dois pontos (haversine / great circle).

    Retorna `None` quando qualquer um dos pontos não possui coordenada válida —
    assim a interface pode simplesmente omitir o "x,x km" em vez de mostrar
    um valor enganoso.

    >>> round(calcular_distancia_km(-23.5505, -46.6333, -23.5629, -46.6544), 1)
    2.4
    """
    if not coordenada_valida(origem_lat, origem_lon):
        return None
    if not coordenada_valida(destino_lat, destino_lon):
        return None

    distancia = great_circle((origem_lat, origem_lon), (destino_lat, destino_lon)).kilometers
    return round(distancia, 2)


def formatar_distancia(distancia_km: float | None) -> str:
    """Formata a distância para exibição no app.

    Abaixo de 1 km mostramos metros, o que fica mais natural na leitura:
        0.35 -> "350 m"   |   4.2 -> "4,2 km"   |   None -> "--"
    """
    if distancia_km is None:
        return "--"
    if distancia_km < 1:
        return f"{int(round(distancia_km * 1000))} m"
    return f"{distancia_km:.1f} km".replace(".", ",")


def chave_ordenacao_distancia(distancia_km: float | None) -> float:
    """Chave de ordenação que joga registros sem coordenada para o fim da lista."""
    return distancia_km if distancia_km is not None else float("inf")
