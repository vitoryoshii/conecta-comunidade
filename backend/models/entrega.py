"""Modelo de Entrega — o agendamento combinado dentro do chat."""

from sqlmodel import Field, SQLModel

from backend.models.enums import StatusEntrega


class Entrega(SQLModel, table=True):
    """Encontro agendado entre doador e solicitante.

    `data` e `hora` são textos simples (ex.: "15/03/2026" e "14:00") porque o
    app apenas exibe o combinado no card destacado do chat — não há fuso ou
    cálculo de agenda envolvido.
    """

    __tablename__ = "entrega"

    id: int | None = Field(default=None, primary_key=True)
    solicitacao_id: int = Field(foreign_key="solicitacao.id", index=True)
    doador_id: int = Field(foreign_key="usuario.id", index=True)

    data: str = Field(max_length=40)
    hora: str = Field(max_length=20)
    local: str = Field(default="", max_length=300)
    status: StatusEntrega = Field(default=StatusEntrega.AGENDADA, index=True)
