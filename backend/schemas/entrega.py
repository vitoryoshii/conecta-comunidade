"""Schemas de entrega (agendamento combinado no chat)."""

from pydantic import BaseModel, ConfigDict, Field

from backend.models.enums import StatusEntrega


class EntregaCriar(BaseModel):
    """Payload de `POST /entregas`."""

    solicitacao_id: int
    data: str = Field(min_length=1, max_length=40)
    hora: str = Field(min_length=1, max_length=20)
    local: str = Field(default="", max_length=300)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "solicitacao_id": 1,
                "data": "15/03/2026",
                "hora": "14:00",
                "local": "Praça Central - São Paulo/SP",
            }
        }
    )


class EntregaAtualizar(BaseModel):
    """Payload de `PATCH /entregas/{id}` — confirma ou cancela o encontro."""

    data: str | None = None
    hora: str | None = None
    local: str | None = None
    status: StatusEntrega | None = None

    model_config = ConfigDict(json_schema_extra={"example": {"status": "realizada"}})


class EntregaLer(BaseModel):
    """Entrega exibida no card destacado do chat."""

    id: int
    solicitacao_id: int
    doador_id: int
    data: str
    hora: str
    local: str
    status: StatusEntrega

    solicitacao_titulo: str = ""
    doador_nome: str = ""

    model_config = ConfigDict(from_attributes=True)
