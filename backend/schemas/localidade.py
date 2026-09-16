"""Schemas das rotas de localidades (estados e municípios do IBGE)."""

from pydantic import BaseModel, ConfigDict


class EstadoLer(BaseModel):
    """Uma unidade federativa na listagem de `GET /localidades/estados`."""

    sigla: str
    nome: str

    model_config = ConfigDict(
        json_schema_extra={"example": {"sigla": "SP", "nome": "São Paulo"}}
    )
