"""
Rotas de ofertas (quem tem item, pode entregar ou oferece ponto de retirada).

A criação de oferta é o destino do botão "Enviar proposta" da tela *Quero
ajudar*: além de registrar a oferta, ela opcionalmente já dispara a primeira
mensagem do chat com o autor da solicitação.
"""

from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import col, select

from backend.deps import SessionDep, UsuarioAtual, UsuarioOpcional
from backend.models import (
    Categoria,
    Mensagem,
    Oferta,
    Solicitacao,
    StatusOferta,
    StatusSolicitacao,
    TipoAjuda,
)
from backend.schemas import OfertaCriar, OfertaLer
from backend.services.apresentacao import (
    carregar_mapa_categorias,
    carregar_mapa_usuarios,
    montar_oferta,
)
from backend.services.geo_service import chave_ordenacao_distancia

router = APIRouter(prefix="/ofertas", tags=["Ofertas"])


@router.get(
    "",
    response_model=list[OfertaLer],
    summary="Listar ofertas",
    description=(
        "Lista as ofertas de ajuda disponíveis, com filtros por categoria, tipo "
        "de ajuda e status. Informe `lat`/`long` para ordenar por proximidade."
    ),
)
def listar_ofertas(
    session: SessionDep,
    usuario: UsuarioOpcional,
    categoria_id: Annotated[int | None, Query(description="Filtra por categoria")] = None,
    tipo_ajuda: Annotated[TipoAjuda | None, Query(description="Filtra pela forma de ajuda")] = None,
    status_filtro: Annotated[
        StatusOferta | None, Query(alias="status", description="Filtra por status")
    ] = None,
    solicitacao_id: Annotated[
        int | None, Query(description="Ofertas feitas para uma solicitação")
    ] = None,
    usuario_id: Annotated[int | None, Query(description="Ofertas de um autor")] = None,
    busca: Annotated[str | None, Query(description="Busca no título e na descrição")] = None,
    lat: Annotated[float | None, Query(description="Latitude do usuário")] = None,
    long: Annotated[float | None, Query(description="Longitude do usuário")] = None,
    ordenar_por: Annotated[
        Literal["distancia", "recentes"], Query(description="Critério de ordenação")
    ] = "distancia",
    limite: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[OfertaLer]:
    """Consulta, filtra, enriquece e ordena as ofertas."""
    consulta = select(Oferta)

    if categoria_id is not None:
        consulta = consulta.where(Oferta.categoria_id == categoria_id)
    if tipo_ajuda is not None:
        consulta = consulta.where(Oferta.tipo_ajuda == tipo_ajuda)
    if status_filtro is not None:
        consulta = consulta.where(Oferta.status == status_filtro)
    if solicitacao_id is not None:
        consulta = consulta.where(Oferta.solicitacao_id == solicitacao_id)
    if usuario_id is not None:
        consulta = consulta.where(Oferta.usuario_id == usuario_id)
    if busca:
        termo = f"%{busca.strip()}%"
        consulta = consulta.where(
            col(Oferta.titulo).ilike(termo) | col(Oferta.descricao).ilike(termo)
        )

    registros = list(session.exec(consulta.order_by(col(Oferta.criada_em).desc())).all())

    categorias = carregar_mapa_categorias(session)
    usuarios = carregar_mapa_usuarios(session, {r.usuario_id for r in registros})

    origem_lat = lat if lat is not None else (usuario.latitude if usuario else None)
    origem_lon = long if long is not None else (usuario.longitude if usuario else None)

    itens = [montar_oferta(r, categorias, usuarios, origem_lat, origem_lon) for r in registros]

    if ordenar_por == "distancia":
        itens.sort(key=lambda i: chave_ordenacao_distancia(i.distancia_km))
    else:
        itens.sort(key=lambda i: -i.criada_em.timestamp())

    return itens[:limite]


@router.post(
    "",
    response_model=OfertaLer,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar proposta de ajuda",
    description=(
        "Cria uma oferta. Quando `solicitacao_id` é informado, o pedido passa "
        "para *em andamento*, o contador de ações do voluntário é incrementado e, "
        "se houver `mensagem`, o chat com o solicitante já nasce com a primeira "
        "fala. **Requer JWT.**"
    ),
)
def criar_oferta(dados: OfertaCriar, usuario: UsuarioAtual, session: SessionDep) -> OfertaLer:
    """Registra a oferta e, opcionalmente, inicia a conversa com o solicitante."""
    if session.get(Categoria, dados.categoria_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Categoria inexistente."
        )

    solicitacao: Solicitacao | None = None
    if dados.solicitacao_id is not None:
        solicitacao = session.get(Solicitacao, dados.solicitacao_id)
        if solicitacao is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Solicitação não encontrada."
            )

    oferta = Oferta(
        usuario_id=usuario.id,  # type: ignore[arg-type]
        titulo=dados.titulo.strip(),
        descricao=dados.descricao,
        categoria_id=dados.categoria_id,
        tipo_ajuda=dados.tipo_ajuda,
        solicitacao_id=dados.solicitacao_id,
        latitude=dados.latitude if dados.latitude is not None else usuario.latitude,
        longitude=dados.longitude if dados.longitude is not None else usuario.longitude,
        endereco=dados.endereco or usuario.cidade,
    )
    session.add(oferta)

    if solicitacao is not None:
        # O pedido sai de "ativa" assim que alguém se propõe a ajudar.
        if solicitacao.status == StatusSolicitacao.ATIVA:
            solicitacao.status = StatusSolicitacao.EM_ANDAMENTO
            session.add(solicitacao)

        # Contador de impacto de quem ajudou.
        usuario.acoes_voluntario += 1
        session.add(usuario)

        # Primeira mensagem do chat, quando o app enviou um texto opcional.
        if dados.mensagem and dados.mensagem.strip():
            session.add(
                Mensagem(
                    remetente_id=usuario.id,  # type: ignore[arg-type]
                    destinatario_id=solicitacao.usuario_id,
                    solicitacao_id=solicitacao.id,
                    texto=dados.mensagem.strip(),
                )
            )

    session.commit()
    session.refresh(oferta)

    return montar_oferta(
        oferta,
        carregar_mapa_categorias(session),
        {usuario.id: usuario},  # type: ignore[dict-item]
        usuario.latitude,
        usuario.longitude,
    )
