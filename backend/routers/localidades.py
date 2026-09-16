"""Rotas de localidades: estados e municípios usados no cadastro."""

from fastapi import APIRouter, HTTPException, status

from backend.schemas import CidadeLer, EstadoLer
from backend.services import localidades_service

router = APIRouter(prefix="/localidades", tags=["Localidades"])


@router.get(
    "/estados",
    response_model=list[EstadoLer],
    summary="Listar estados",
    description=(
        "Os 27 estados (26 + Distrito Federal), ordenados por nome. Os dados vêm "
        "de um arquivo gerado a partir do IBGE e versionado com o código — a API "
        "não consulta o serviço do IBGE em tempo de execução."
    ),
)
def listar_estados() -> list[dict[str, str]]:
    """Devolve sigla e nome de cada UF."""
    return localidades_service.listar_estados()


@router.get(
    "/estados/{sigla}/cidades",
    response_model=list[CidadeLer],
    summary="Listar cidades de um estado",
    description=(
        "Municípios da UF informada, em ordem alfabética, cada um com a "
        "latitude/longitude da sede — é o que o cadastro grava como localização "
        "do usuário."
    ),
    responses={404: {"description": "Sigla de estado desconhecida."}},
)
def listar_cidades(sigla: str) -> list[dict]:
    """Devolve os municípios da UF, ou 404 quando a sigla não existe."""
    cidades = localidades_service.listar_cidades(sigla)
    if cidades is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estado '{sigla}' não encontrado.",
        )
    return cidades
