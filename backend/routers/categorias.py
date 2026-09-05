"""Rotas de categorias — alimentam a grade da Home e os filtros de busca."""

from fastapi import APIRouter
from sqlmodel import select

from backend.deps import SessionDep
from backend.models import Categoria
from backend.schemas import CategoriaLer

router = APIRouter(prefix="/categorias", tags=["Categorias"])


@router.get(
    "",
    response_model=list[CategoriaLer],
    summary="Listar categorias",
    description="Lista todas as categorias de ajuda com o nome do ícone usado no app.",
)
def listar_categorias(session: SessionDep) -> list[Categoria]:
    """Retorna as categorias em ordem alfabética."""
    return list(session.exec(select(Categoria).order_by(Categoria.nome)).all())
