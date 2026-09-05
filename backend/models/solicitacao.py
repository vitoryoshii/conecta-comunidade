"""Modelo de Solicitação — o pedido de ajuda publicado por um usuário."""

from datetime import datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from backend.models.enums import StatusSolicitacao, Urgencia
from backend.models.usuario import agora_utc


class Solicitacao(SQLModel, table=True):
    """Pedido de ajuda georreferenciado.

    A flag `emergencia` ativa o "modo emergência": a solicitação é fixada no
    topo das listagens e recebe destaque no mapa, independentemente da distância.
    """

    __tablename__ = "solicitacao"

    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True)

    titulo: str = Field(index=True, max_length=160)
    descricao: str = Field(default="", max_length=3000)
    categoria_id: int = Field(foreign_key="categoria.id", index=True)

    quantidade: str = Field(default="", max_length=120)  # ex.: "20 litros"
    urgencia: Urgencia = Field(default=Urgencia.MEDIA, index=True)
    status: StatusSolicitacao = Field(default=StatusSolicitacao.ATIVA, index=True)
    pessoas_beneficiadas: int = Field(default=1)

    # Localização do pedido (usada no cálculo de distância e nos pins do mapa).
    latitude: float = Field(default=0.0)
    longitude: float = Field(default=0.0)
    endereco: str = Field(default="", max_length=300)

    # Galeria de fotos: lista de URLs armazenada como JSON.
    fotos: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    emergencia: bool = Field(default=False, index=True)
    criada_em: datetime = Field(default_factory=agora_utc, index=True)
