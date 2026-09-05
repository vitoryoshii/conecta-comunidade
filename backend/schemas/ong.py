"""Schemas de ONG."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ONGLer(BaseModel):
    """Instituição com distância já calculada em relação ao usuário."""

    id: int
    nome: str
    descricao: str
    avaliacao: float
    total_avaliacoes: int
    verificada: bool
    recursos_disponiveis: list[dict[str, Any]]
    endereco: str
    latitude: float
    longitude: float
    avatar_url: str | None = None

    # --- Campos derivados --------------------------------------------------
    distancia_km: float | None = None
    distancia_formatada: str = "--"

    model_config = ConfigDict(from_attributes=True)


class AvaliacaoCriar(BaseModel):
    """Payload de `POST /ongs/{id}/avaliar` — nota de 1 a 5 estrelas."""

    nota: int = Field(ge=1, le=5)

    model_config = ConfigDict(json_schema_extra={"example": {"nota": 5}})
