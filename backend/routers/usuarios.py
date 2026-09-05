"""Rotas de perfil do usuário e dos números de "Meu impacto"."""

from fastapi import APIRouter, HTTPException, status
from sqlmodel import func, select

from backend.deps import SessionDep, UsuarioAtual
from backend.models import Oferta, Solicitacao, StatusSolicitacao, Usuario
from backend.schemas import ImpactoLer, UsuarioAtualizar, UsuarioLer

router = APIRouter(prefix="/usuarios", tags=["Usuários"])
router_perfil = APIRouter(prefix="/perfil", tags=["Usuários"])


@router.get(
    "/{usuario_id}",
    response_model=UsuarioLer,
    summary="Perfil público",
    description="Dados públicos de um usuário (usado no chat e no detalhe da solicitação).",
)
def obter_usuario(usuario_id: int, session: SessionDep) -> Usuario:
    """Busca um usuário pelo id."""
    usuario = session.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return usuario


@router.patch(
    "/me",
    response_model=UsuarioLer,
    summary="Editar meu perfil",
    description="Atualiza nome, cidade, coordenadas ou avatar do usuário logado.",
)
def atualizar_meu_perfil(
    dados: UsuarioAtualizar, usuario: UsuarioAtual, session: SessionDep
) -> Usuario:
    """Aplica apenas os campos enviados (patch parcial)."""
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(usuario, campo, valor)

    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@router_perfil.get(
    "/impacto",
    response_model=ImpactoLer,
    summary="Meu impacto",
    description=(
        "Números exibidos no perfil: contadores acumulados do usuário somados a "
        "totais calculados na hora (solicitações criadas, ofertas e pessoas beneficiadas)."
    ),
)
def meu_impacto(usuario: UsuarioAtual, session: SessionDep) -> ImpactoLer:
    """Consolida os indicadores de impacto do usuário logado."""
    total_solicitacoes = session.exec(
        select(func.count()).select_from(Solicitacao).where(Solicitacao.usuario_id == usuario.id)
    ).one()

    total_ofertas = session.exec(
        select(func.count()).select_from(Oferta).where(Oferta.usuario_id == usuario.id)
    ).one()

    # Soma de pessoas beneficiadas nas solicitações do usuário já concluídas.
    pessoas = session.exec(
        select(func.coalesce(func.sum(Solicitacao.pessoas_beneficiadas), 0)).where(
            Solicitacao.usuario_id == usuario.id,
            Solicitacao.status == StatusSolicitacao.CONCLUIDA,
        )
    ).one()

    return ImpactoLer(
        solicitacoes_atendidas=usuario.solicitacoes_atendidas,
        doacoes_recebidas=usuario.doacoes_recebidas,
        acoes_voluntario=usuario.acoes_voluntario,
        total_solicitacoes_criadas=int(total_solicitacoes),
        total_ofertas_criadas=int(total_ofertas),
        pessoas_beneficiadas=int(pessoas),
    )
