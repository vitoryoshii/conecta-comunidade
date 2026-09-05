"""Schemas de categoria."""

from pydantic import BaseModel, ConfigDict


class CategoriaLer(BaseModel):
    """Categoria exibida na grade da Home e nos filtros."""

    id: int
    nome: str
    icone: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {"id": 2, "nome": "Alimentos", "icone": "restaurant"}},
    )
