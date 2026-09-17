"""
Rotas de favoritos — os pedidos que o usuário guardou para depois.

A lista devolve as **solicitações inteiras**, no mesmo schema da Home e do
Explorar, e não apenas os ids: assim a tela de Favoritos reusa exatamente o
mesmo cartão, sem uma segunda requisição por item.
"""

from fastapi import APIRouter, HTTPException, Response, status
from sqlmodel import select

from backend.deps import SessionDep, UsuarioAtual
from backend.models import Favorito, Solicitacao
from backend.schemas import FavoritoCriar, FavoritoLer, SolicitacaoLer
from backend.services.apresentacao import (
    carregar_mapa_categorias,
    carregar_mapa_usuarios,
    montar_solicitacao,
)

router = APIRouter(prefix="/favoritos", tags=["Favoritos"])


@router.get(
    "",
    response_model=list[SolicitacaoLer],
    summary="Meus favoritos",
    description=(
        "Solicitações favoritadas pelo usuário logado, das mais recentes para as "
        "mais antigas — no mesmo formato da listagem de solicitações."
    ),
)
def listar_favoritos(usuario: UsuarioAtual, session: SessionDep) -> list[SolicitacaoLer]:
    """Lista as solicitações guardadas, já prontas para o cartão do app."""
    favoritos = session.exec(
        select(Favorito)
        .where(Favorito.usuario_id == usuario.id)
        .order_by(Favorito.criado_em.desc())  # type: ignore[attr-defined]
    ).all()

    ids = [favorito.solicitacao_id for favorito in favoritos]
    if not ids:
        return []

    encontradas = {
        solicitacao.id: solicitacao
        for solicitacao in session.exec(
            select(Solicitacao).where(Solicitacao.id.in_(ids))  # type: ignore[attr-defined,union-attr]
        ).all()
    }

    categorias = carregar_mapa_categorias(session)
    usuarios = carregar_mapa_usuarios(
        session, {s.usuario_id for s in encontradas.values()}
    )

    # A ordem é a dos favoritos (mais recente primeiro), não a do banco.
    return [
        montar_solicitacao(
            encontradas[id_],
            categorias,
            usuarios,
            usuario.latitude,
            usuario.longitude,
            favoritada=True,
        )
        for id_ in ids
        if id_ in encontradas
    ]



@router.post(
    "",
    response_model=FavoritoLer,
    status_code=status.HTTP_201_CREATED,
    summary="Favoritar",
    description=(
        "Guarda uma solicitação. Favoritar o que já está guardado devolve o "
        "favorito existente (201 de novo) em vez de erro: o coração da tela é um "
        "botão que alterna, e dois toques rápidos não podem virar falha."
    ),
)
def favoritar(
    dados: FavoritoCriar, usuario: UsuarioAtual, session: SessionDep
) -> Favorito:
    """Cria (ou reaproveita) a marcação de favorito."""
    solicitacao = session.get(Solicitacao, dados.solicitacao_id)
    if solicitacao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Solicitação não encontrada."
        )

    existente = session.exec(
        select(Favorito).where(
            Favorito.usuario_id == usuario.id,
            Favorito.solicitacao_id == dados.solicitacao_id,
        )
    ).first()
    if existente:
        return existente

    favorito = Favorito(usuario_id=usuario.id, solicitacao_id=dados.solicitacao_id)  # type: ignore[arg-type]
    session.add(favorito)
    session.commit()
    session.refresh(favorito)
    return favorito


@router.delete(
    "/{solicitacao_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desfavoritar",
    description=(
        "Remove a solicitação dos favoritos. Desfavoritar o que não está "
        "guardado também responde 204 — o resultado desejado já é o estado atual."
    ),
)
def desfavoritar(
    solicitacao_id: int, usuario: UsuarioAtual, session: SessionDep
) -> Response:
    """Apaga a marcação, se ela existir."""
    favorito = session.exec(
        select(Favorito).where(
            Favorito.usuario_id == usuario.id,
            Favorito.solicitacao_id == solicitacao_id,
        )
    ).first()

    if favorito is not None:
        session.delete(favorito)
        session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
