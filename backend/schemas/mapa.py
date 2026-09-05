"""Schemas da tela de Mapa."""

from pydantic import BaseModel, ConfigDict

from backend.models.enums import TipoPontoMapa


class PontoMapa(BaseModel):
    """Pin exibido no mapa.

    Um único formato atende os quatro tipos de pin (ajuda, oferecendo, ONG e
    ponto de retirada), o que simplifica a renderização e os filtros no app.
    """

    id: int
    tipo: TipoPontoMapa
    titulo: str
    subtitulo: str = ""
    latitude: float
    longitude: float
    urgencia: str | None = None
    emergencia: bool = False
    verificada: bool = False
    distancia_km: float | None = None
    distancia_formatada: str = "--"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "tipo": "ajuda",
                "titulo": "Água potável para 4 famílias",
                "subtitulo": "Água · 16 pessoas",
                "latitude": -23.5610,
                "longitude": -46.6560,
                "urgencia": "alta",
                "emergencia": True,
                "distancia_formatada": "1,2 km",
            }
        }
    )


class RespostaMapa(BaseModel):
    """Coleção de pins + contagem por tipo (alimenta o painel de filtros)."""

    pontos: list[PontoMapa]
    total_por_tipo: dict[str, int]
