"""Modelo de Categoria — agrupa solicitações e ofertas por tipo de necessidade."""

from sqlmodel import Field, SQLModel


class Categoria(SQLModel, table=True):
    """Categoria de ajuda (Água, Alimentos, Roupas, ...).

    O campo `icone` guarda o nome de um ícone do Material Icons, consumido
    diretamente pelo Flet na grade de categorias da Home.
    """

    __tablename__ = "categoria"

    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(unique=True, index=True, max_length=80)
    icone: str = Field(default="category", max_length=60)
