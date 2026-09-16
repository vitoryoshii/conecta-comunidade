"""Schemas das rotas de localidades (estados e municípios do IBGE)."""

from pydantic import BaseModel, ConfigDict


class EstadoLer(BaseModel):
    """Uma unidade federativa na listagem de `GET /localidades/estados`."""

    sigla: str
    nome: str

    model_config = ConfigDict(
        json_schema_extra={"example": {"sigla": "SP", "nome": "São Paulo"}}
    )


class CidadeLer(BaseModel):
    """Um município na listagem de `GET /localidades/estados/{sigla}/cidades`.

    As coordenadas são as da sede e alimentam a localização do usuário no
    cadastro — é delas que sai o cálculo de distância.
    """

    nome: str
    lat: float
    lng: float

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"nome": "Salvador", "lat": -12.9718, "lng": -38.5011}
        }
    )
