"""
Rotas de entregas.

A entrega nasce no chat: quando doador e solicitante combinam dia, hora e local,
o app cria o registro e o card destacado de "Entrega agendada" passa a aparecer
no topo da conversa.
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import Session, col, or_, select

from backend.deps import SessionDep, UsuarioAtual
from backend.models import Entrega, Solicitacao, StatusEntrega, StatusSolicitacao, Usuario
from backend.schemas import EntregaAtualizar, EntregaCriar, EntregaLer

router = APIRouter(prefix="/entregas", tags=["Entregas"])


def _montar_entrega(entrega: Entrega, session: Session) -> EntregaLer:
    """Acrescenta título da solicitação e nome do doador ao schema de leitura."""
    solicitacao = session.get(Solicitacao, entrega.solicitacao_id)
    doador = session.get(Usuario, entrega.doador_id)
    return EntregaLer(
        **entrega.model_dump(),
        solicitacao_titulo=solicitacao.titulo if solicitacao else "",
        doador_nome=doador.nome if doador else "",
    )


@router.get(
    "",
    response_model=list[EntregaLer],
    summary="Listar entregas",
    description=(
        "Entregas em que o usuário logado participa — como doador ou como autor "
        "da solicitação. Use `solicitacao_id` para buscar o agendamento de um "
        "chat específico. **Requer JWT.**"
    ),
)
def listar_entregas(
    usuario: UsuarioAtual,
    session: SessionDep,
    solicitacao_id: Annotated[int | None, Query(description="Filtra por solicitação")] = None,
    status_filtro: Annotated[
        StatusEntrega | None, Query(alias="status", description="Filtra por status")
    ] = None,
) -> list[EntregaLer]:
    """Lista as entregas visíveis para o usuário."""
    # Ids das solicitações criadas pelo próprio usuário: ele também enxerga as
    # entregas agendadas por terceiros para os seus pedidos.
    minhas_solicitacoes = [
        solicitacao.id
        for solicitacao in session.exec(
            select(Solicitacao).where(Solicitacao.usuario_id == usuario.id)
        ).all()
    ] or [-1]

    consulta = select(Entrega).where(
        or_(
            col(Entrega.doador_id) == usuario.id,
            col(Entrega.solicitacao_id).in_(minhas_solicitacoes),
        )
    )
    if solicitacao_id is not None:
        consulta = consulta.where(Entrega.solicitacao_id == solicitacao_id)
    if status_filtro is not None:
        consulta = consulta.where(Entrega.status == status_filtro)

    return [_montar_entrega(e, session) for e in session.exec(consulta).all()]


@router.post(
    "",
    response_model=EntregaLer,
    status_code=status.HTTP_201_CREATED,
    summary="Agendar entrega",
    description=(
        "Cria o agendamento combinado no chat e move a solicitação para "
        "*em andamento*. **Requer JWT.**"
    ),
)
def criar_entrega(dados: EntregaCriar, usuario: UsuarioAtual, session: SessionDep) -> EntregaLer:
    """Agenda a entrega em nome do usuário logado (o doador)."""
    solicitacao = session.get(Solicitacao, dados.solicitacao_id)
    if solicitacao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Solicitação não encontrada."
        )

    entrega = Entrega(
        solicitacao_id=dados.solicitacao_id,
        doador_id=usuario.id,  # type: ignore[arg-type]
        data=dados.data,
        hora=dados.hora,
        local=dados.local or solicitacao.endereco,
    )
    session.add(entrega)

    if solicitacao.status == StatusSolicitacao.ATIVA:
        solicitacao.status = StatusSolicitacao.EM_ANDAMENTO
        session.add(solicitacao)

    session.commit()
    session.refresh(entrega)
    return _montar_entrega(entrega, session)


@router.patch(
    "/{entrega_id}",
    response_model=EntregaLer,
    summary="Atualizar entrega",
    description=(
        "Reagenda, confirma ou cancela a entrega. Ao marcar como *realizada*, a "
        "solicitação é concluída e os contadores de impacto de ambos os lados "
        "são atualizados. **Requer JWT.**"
    ),
)
def atualizar_entrega(
    entrega_id: int, dados: EntregaAtualizar, usuario: UsuarioAtual, session: SessionDep
) -> EntregaLer:
    """Aplica o patch e propaga os efeitos no impacto dos participantes."""
    entrega = session.get(Entrega, entrega_id)
    if entrega is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrega não encontrada.")

    solicitacao = session.get(Solicitacao, entrega.solicitacao_id)
    participantes = {entrega.doador_id, solicitacao.usuario_id if solicitacao else None}
    if usuario.id not in participantes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Somente os participantes podem alterar esta entrega.",
        )

    alteracoes = dados.model_dump(exclude_unset=True)
    virou_realizada = (
        alteracoes.get("status") == StatusEntrega.REALIZADA
        and entrega.status != StatusEntrega.REALIZADA
    )

    for campo, valor in alteracoes.items():
        setattr(entrega, campo, valor)
    session.add(entrega)

    if virou_realizada and solicitacao is not None:
        solicitacao.status = StatusSolicitacao.CONCLUIDA
        session.add(solicitacao)

        doador = session.get(Usuario, entrega.doador_id)
        if doador is not None:
            doador.solicitacoes_atendidas += 1
            session.add(doador)

        solicitante = session.get(Usuario, solicitacao.usuario_id)
        if solicitante is not None:
            solicitante.doacoes_recebidas += 1
            session.add(solicitante)

    session.commit()
    session.refresh(entrega)
    return _montar_entrega(entrega, session)
