"""Modelo de ONG — instituições parceiras exibidas no app e no mapa."""

from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class ONG(SQLModel, table=True):
    """Instituição cadastrada na plataforma.

    `recursos_disponiveis` é uma lista JSON no formato:
        [{"nome": "Cestas básicas", "quantidade": 120, "icone": "shopping_basket"}]
    exibida como cards na tela de Perfil da ONG.
    """

    __tablename__ = "ong"

    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(index=True, max_length=160)
    descricao: str = Field(default="", max_length=2000)

    # Reputação: média das avaliações e quantidade de avaliações recebidas.
    avaliacao: float = Field(default=0.0)
    total_avaliacoes: int = Field(default=0)

    # Selo de verificação exibido ao lado do nome.
    verificada: bool = Field(default=False, index=True)

    recursos_disponiveis: list[dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSON)
    )

    endereco: str = Field(default="", max_length=300)
    latitude: float = Field(default=0.0)
    longitude: float = Field(default=0.0)
    avatar_url: str | None = Field(default=None, max_length=500)
