"""Schemas de favoritos."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FavoritoCriar(BaseModel):
    """Payload de `POST /favoritos`."""

    solicitacao_id: int

    model_config = ConfigDict(json_schema_extra={"example": {"solicitacao_id": 3}})


class FavoritoLer(BaseModel):
    """Confirmação de que a solicitação está guardada."""

    solicitacao_id: int
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)
