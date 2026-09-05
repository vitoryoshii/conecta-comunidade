"""
Rotas de solicitações (pedidos de ajuda).

Este é o coração da API: alimenta a Home ("solicitações próximas de você"), a
tela Explorar (busca + filtros) e o detalhe do pedido. A ordenação por distância
é feita em Python, depois da consulta, porque o cálculo de haversine não existe
nativamente no SQLite.
"""

from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import col, select

from backend.deps import SessionDep, UsuarioAtual, UsuarioOpcional
from backend.models import Categoria, Solicitacao, StatusSolicitacao, Urgencia, Usuario
from backend.schemas import SolicitacaoAtualizar, SolicitacaoCriar, SolicitacaoLer
from backend.services.apresentacao import (
    carregar_mapa_categorias,
    carregar_mapa_usuarios,
    montar_solicitacao,
)
from backend.services.geo_service import chave_ordenacao_distancia

router = APIRouter(prefix="/solicitacoes", tags=["Solicitações"])

# Peso de cada nível de urgência para a ordenação "urgencia" (maior = primeiro).
PESO_URGENCIA = {Urgencia.ALTA: 3, Urgencia.MEDIA: 2, Urgencia.BAIXA: 1}


def _coordenadas_de_referencia(
    lat: float | None, lon: float | None, usuario: Usuario | None
) -> tuple[float | None, float | None]:
    """Define a origem do cálculo de distância.

    Prioriza as coordenadas enviadas na query string (o app pode usar o GPS) e,
    na ausência delas, cai para a localização cadastrada do usuário logado.
    """
    if lat is not None and lon is not None:
        return lat, lon
    if usuario is not None:
        return usuario.latitude, usuario.longitude
    return None, None


@router.get(
    "",
    response_model=list[SolicitacaoLer],
    summary="Listar solicitações",
    description=(
        "Lista pedidos de ajuda com filtros por categoria, urgência, status, "
        "emergência e texto livre. Informe `lat`/`long` para receber a distância "
        "em km e ordenar por proximidade. Solicitações em **modo emergência** "
        "são sempre fixadas no topo."
    ),
)
def listar_solicitacoes(
    session: SessionDep,
    usuario: UsuarioOpcional,
    categoria_id: Annotated[int | None, Query(description="Filtra por categoria")] = None,
    urgencia: Annotated[Urgencia | None, Query(description="Filtra por urgência")] = None,
    status_filtro: Annotated[
        StatusSolicitacao | None, Query(alias="status", description="Filtra por status")
    ] = None,
    emergencia: Annotated[bool | None, Query(description="Somente modo emergência")] = None,
    busca: Annotated[str | None, Query(description="Busca no título e na descrição")] = None,
    usuario_id: Annotated[int | None, Query(description="Somente de um autor")] = None,
    lat: Annotated[float | None, Query(description="Latitude do usuário")] = None,
    long: Annotated[float | None, Query(description="Longitude do usuário")] = None,
    ordenar_por: Annotated[
        Literal["distancia", "recentes", "urgencia"],
        Query(description="Critério de ordenação"),
    ] = "distancia",
    limite: Annotated[int, Query(ge=1, le=200, description="Máximo de itens")] = 50,
) -> list[SolicitacaoLer]:
    """Consulta, filtra, enriquece e ordena as solicitações."""
    consulta = select(Solicitacao)

    if categoria_id is not None:
        consulta = consulta.where(Solicitacao.categoria_id == categoria_id)
    if urgencia is not None:
        consulta = consulta.where(Solicitacao.urgencia == urgencia)
    if status_filtro is not None:
        consulta = consulta.where(Solicitacao.status == status_filtro)
    if emergencia is not None:
        consulta = consulta.where(Solicitacao.emergencia == emergencia)
    if usuario_id is not None:
        consulta = consulta.where(Solicitacao.usuario_id == usuario_id)
    if busca:
        termo = f"%{busca.strip()}%"
        consulta = consulta.where(
            col(Solicitacao.titulo).ilike(termo) | col(Solicitacao.descricao).ilike(termo)
        )

    registros = list(session.exec(consulta.order_by(col(Solicitacao.criada_em).desc())).all())

    # Enriquecimento: categoria, autor, distância e tempo de publicação.
    categorias = carregar_mapa_categorias(session)
    usuarios = carregar_mapa_usuarios(session, {r.usuario_id for r in registros})
    origem_lat, origem_lon = _coordenadas_de_referencia(lat, long, usuario)

    itens = [
        montar_solicitacao(registro, categorias, usuarios, origem_lat, origem_lon)
        for registro in registros
    ]

    # Ordenação: o modo emergência sempre vem primeiro, depois o critério pedido.
    if ordenar_por == "distancia":
        itens.sort(key=lambda i: (not i.emergencia, chave_ordenacao_distancia(i.distancia_km)))
    elif ordenar_por == "urgencia":
        itens.sort(key=lambda i: (not i.emergencia, -PESO_URGENCIA[i.urgencia], -i.id))
    else:  # "recentes"
        itens.sort(key=lambda i: (not i.emergencia, -i.criada_em.timestamp()))

    return itens[:limite]


@router.get(
    "/{solicitacao_id}",
    response_model=SolicitacaoLer,
    summary="Detalhe da solicitação",
    description="Retorna um pedido específico já com distância e dados do autor.",
)
def obter_solicitacao(
    solicitacao_id: int,
    session: SessionDep,
    usuario: UsuarioOpcional,
    lat: Annotated[float | None, Query()] = None,
    long: Annotated[float | None, Query()] = None,
) -> SolicitacaoLer:
    """Busca uma solicitação pelo id."""
    registro = session.get(Solicitacao, solicitacao_id)
    if registro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Solicitação não encontrada."
        )

    origem_lat, origem_lon = _coordenadas_de_referencia(lat, long, usuario)
    return montar_solicitacao(
        registro,
        carregar_mapa_categorias(session),
        carregar_mapa_usuarios(session, {registro.usuario_id}),
        origem_lat,
        origem_lon,
    )


@router.post(
    "",
    response_model=SolicitacaoLer,
    status_code=status.HTTP_201_CREATED,
    summary="Publicar solicitação",
    description="Cria um pedido de ajuda vinculado ao usuário autenticado. **Requer JWT.**",
)
def criar_solicitacao(
    dados: SolicitacaoCriar, usuario: UsuarioAtual, session: SessionDep
) -> SolicitacaoLer:
    """Cria a solicitação, herdando a localização do usuário quando não informada."""
    if session.get(Categoria, dados.categoria_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Categoria inexistente."
        )

    registro = Solicitacao(
        usuario_id=usuario.id,  # type: ignore[arg-type]
        titulo=dados.titulo.strip(),
        descricao=dados.descricao,
        categoria_id=dados.categoria_id,
        quantidade=dados.quantidade,
        urgencia=dados.urgencia,
        pessoas_beneficiadas=dados.pessoas_beneficiadas,
        latitude=dados.latitude if dados.latitude is not None else usuario.latitude,
        longitude=dados.longitude if dados.longitude is not None else usuario.longitude,
        endereco=dados.endereco or usuario.cidade,
        fotos=dados.fotos,
        emergencia=dados.emergencia,
    )
    session.add(registro)
    session.commit()
    session.refresh(registro)

    return montar_solicitacao(
        registro,
        carregar_mapa_categorias(session),
        {usuario.id: usuario},  # type: ignore[dict-item]
        usuario.latitude,
        usuario.longitude,
    )


@router.patch(
    "/{solicitacao_id}",
    response_model=SolicitacaoLer,
    summary="Atualizar solicitação",
    description=(
        "Edita campos do pedido — usado principalmente para mudar o status nas "
        "abas de *Minhas solicitações*. Somente o autor pode alterar. **Requer JWT.**"
    ),
)
def atualizar_solicitacao(
    solicitacao_id: int,
    dados: SolicitacaoAtualizar,
    usuario: UsuarioAtual,
    session: SessionDep,
) -> SolicitacaoLer:
    """Aplica um patch parcial na solicitação do próprio usuário."""
    registro = session.get(Solicitacao, solicitacao_id)
    if registro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Solicitação não encontrada."
        )
    if registro.usuario_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Somente o autor pode editar esta solicitação.",
        )

    alteracoes = dados.model_dump(exclude_unset=True)
    virou_concluida = (
        alteracoes.get("status") == StatusSolicitacao.CONCLUIDA
        and registro.status != StatusSolicitacao.CONCLUIDA
    )

    for campo, valor in alteracoes.items():
        setattr(registro, campo, valor)

    # Ao concluir um pedido, o autor registra uma "doação recebida" no impacto.
    if virou_concluida:
        usuario.doacoes_recebidas += 1
        session.add(usuario)

    session.add(registro)
    session.commit()
    session.refresh(registro)

    return montar_solicitacao(
        registro,
        carregar_mapa_categorias(session),
        carregar_mapa_usuarios(session, {registro.usuario_id}),
        usuario.latitude,
        usuario.longitude,
    )
