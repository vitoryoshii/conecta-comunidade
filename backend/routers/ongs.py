"""
Rotas de ONGs e instituições.

Alimenta a lista "ONGs e Instituições" (busca, estrelas, selo de verificação e
distância) e a tela de Perfil da ONG, com os cards de recursos disponíveis.
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import col, select

from backend.deps import SessionDep, UsuarioAtual, UsuarioOpcional
from backend.models import ONG
from backend.schemas import AvaliacaoCriar, ONGLer
from backend.services.geo_service import (
    calcular_distancia_km,
    chave_ordenacao_distancia,
    formatar_distancia,
)

router = APIRouter(prefix="/ongs", tags=["ONGs"])


def _montar_ong(ong: ONG, origem_lat: float | None, origem_lon: float | None) -> ONGLer:
    """Converte a entidade em schema de leitura, acrescentando a distância."""
    distancia = calcular_distancia_km(origem_lat, origem_lon, ong.latitude, ong.longitude)
    return ONGLer(
        **ong.model_dump(),
        distancia_km=distancia,
        distancia_formatada=formatar_distancia(distancia),
    )


@router.get(
    "",
    response_model=list[ONGLer],
    summary="Listar ONGs",
    description=(
        "Lista instituições com busca por nome/descrição, filtro de verificadas "
        "e distância calculada a partir de `lat`/`long` (ou da cidade do usuário logado)."
    ),
)
def listar_ongs(
    session: SessionDep,
    usuario: UsuarioOpcional,
    busca: Annotated[str | None, Query(description="Busca por nome ou descrição")] = None,
    somente_verificadas: Annotated[
        bool, Query(description="Retorna apenas ONGs com selo de verificação")
    ] = False,
    lat: Annotated[float | None, Query(description="Latitude do usuário")] = None,
    long: Annotated[float | None, Query(description="Longitude do usuário")] = None,
    limite: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[ONGLer]:
    """Retorna as ONGs ordenadas por proximidade."""
    consulta = select(ONG)

    if somente_verificadas:
        consulta = consulta.where(ONG.verificada == True)  # noqa: E712 (necessário no SQLAlchemy)
    if busca:
        termo = f"%{busca.strip()}%"
        consulta = consulta.where(col(ONG.nome).ilike(termo) | col(ONG.descricao).ilike(termo))

    registros = list(session.exec(consulta).all())

    origem_lat = lat if lat is not None else (usuario.latitude if usuario else None)
    origem_lon = long if long is not None else (usuario.longitude if usuario else None)

    itens = [_montar_ong(ong, origem_lat, origem_lon) for ong in registros]
    itens.sort(key=lambda i: chave_ordenacao_distancia(i.distancia_km))
    return itens[:limite]


@router.get(
    "/{ong_id}",
    response_model=ONGLer,
    summary="Perfil da ONG",
    description="Detalhe da instituição, incluindo os recursos disponíveis e a avaliação média.",
)
def obter_ong(
    ong_id: int,
    session: SessionDep,
    usuario: UsuarioOpcional,
    lat: Annotated[float | None, Query()] = None,
    long: Annotated[float | None, Query()] = None,
) -> ONGLer:
    """Busca uma ONG pelo id."""
    ong = session.get(ONG, ong_id)
    if ong is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ONG não encontrada.")

    origem_lat = lat if lat is not None else (usuario.latitude if usuario else None)
    origem_lon = long if long is not None else (usuario.longitude if usuario else None)
    return _montar_ong(ong, origem_lat, origem_lon)


@router.post(
    "/{ong_id}/avaliar",
    response_model=ONGLer,
    summary="Avaliar ONG",
    description=(
        "Registra uma nota de 1 a 5 estrelas e recalcula a média incremental "
        "(`nova_media = (media * total + nota) / (total + 1)`). **Requer JWT.**"
    ),
)
def avaliar_ong(
    ong_id: int, dados: AvaliacaoCriar, usuario: UsuarioAtual, session: SessionDep
) -> ONGLer:
    """Atualiza a média e o total de avaliações da instituição."""
    ong = session.get(ONG, ong_id)
    if ong is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ONG não encontrada.")

    soma_atual = ong.avaliacao * ong.total_avaliacoes
    ong.total_avaliacoes += 1
    ong.avaliacao = round((soma_atual + dados.nota) / ong.total_avaliacoes, 2)

    session.add(ong)
    session.commit()
    session.refresh(ong)

    return _montar_ong(ong, usuario.latitude, usuario.longitude)
