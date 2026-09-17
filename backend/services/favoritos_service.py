"""
Consulta de favoritos usada pelas listagens.

As telas mostram o coração preenchido nos pedidos que o usuário guardou. Buscar
isso por cartão seria uma consulta por item (o clássico N+1); aqui os ids vêm
todos de uma vez, e cada montagem só checa se o id está no conjunto.
"""

from sqlmodel import Session, select

from backend.models import Favorito, Usuario


def ids_favoritados(
    session: Session, usuario: Usuario | None, solicitacao_ids: list[int] | None = None
) -> set[int]:
    """Ids das solicitações que este usuário favoritou.

    Sem sessão não há favorito: visitante recebe o conjunto vazio, e todos os
    corações aparecem apagados. `solicitacao_ids` limita a consulta ao que está
    na tela — na listagem, é o que evita carregar a lista inteira de favoritos.
    """
    if usuario is None or usuario.id is None:
        return set()

    consulta = select(Favorito.solicitacao_id).where(Favorito.usuario_id == usuario.id)
    if solicitacao_ids is not None:
        if not solicitacao_ids:
            return set()
        consulta = consulta.where(Favorito.solicitacao_id.in_(solicitacao_ids))  # type: ignore[attr-defined]

    return set(session.exec(consulta).all())
