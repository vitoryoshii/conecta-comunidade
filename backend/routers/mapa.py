"""
Rota do mapa.

Consolida quatro fontes distintas (solicitações, ofertas, pontos de retirada e
ONGs) em uma única lista de pins com o mesmo formato, o que deixa o app livre
para desenhar e filtrar os marcadores sem conhecer as regras de cada entidade.
"""

from typing import Annotated

from fastapi import APIRouter, Query
from sqlmodel import select

from backend.deps import SessionDep, UsuarioOpcional
from backend.models import ONG, Oferta, Solicitacao, StatusOferta, StatusSolicitacao, TipoAjuda
from backend.models.enums import TipoPontoMapa
from backend.schemas import PontoMapa, RespostaMapa
from backend.services.apresentacao import carregar_mapa_categorias
from backend.services.geo_service import (
    calcular_distancia_km,
    chave_ordenacao_distancia,
    coordenada_valida,
    formatar_distancia,
)

router = APIRouter(prefix="/mapa", tags=["Mapa"])


@router.get(
    "",
    response_model=RespostaMapa,
    summary="Pontos do mapa",
    description=(
        "Retorna os pins do mapa em um formato único. Os tipos podem ser "
        "filtrados por `tipos` (repetindo o parâmetro, ex.: `?tipos=ajuda&tipos=ong`) "
        "e cada pin traz a distância em relação a `lat`/`long`. Pins de "
        "**modo emergência** vêm sempre no início da lista."
    ),
)
def pontos_do_mapa(
    session: SessionDep,
    usuario: UsuarioOpcional,
    tipos: Annotated[
        list[TipoPontoMapa] | None,
        Query(description="Tipos de pin a incluir; omitir traz todos"),
    ] = None,
    lat: Annotated[float | None, Query(description="Latitude do usuário")] = None,
    long: Annotated[float | None, Query(description="Longitude do usuário")] = None,
    raio_km: Annotated[
        float | None, Query(gt=0, description="Limita os pins a um raio em km")
    ] = None,
) -> RespostaMapa:
    """Monta a lista de pins aplicando os filtros de tipo e de raio."""
    tipos_desejados = set(tipos) if tipos else set(TipoPontoMapa)

    origem_lat = lat if lat is not None else (usuario.latitude if usuario else None)
    origem_lon = long if long is not None else (usuario.longitude if usuario else None)
    categorias = carregar_mapa_categorias(session)

    pontos: list[PontoMapa] = []

    def adicionar(
        *,
        id_: int,
        tipo: TipoPontoMapa,
        titulo: str,
        subtitulo: str,
        latitude: float,
        longitude: float,
        urgencia: str | None = None,
        emergencia: bool = False,
        verificada: bool = False,
    ) -> None:
        """Cria o pin já com a distância calculada (ignora coordenadas inválidas)."""
        if not coordenada_valida(latitude, longitude):
            return
        distancia = calcular_distancia_km(origem_lat, origem_lon, latitude, longitude)
        pontos.append(
            PontoMapa(
                id=id_,
                tipo=tipo,
                titulo=titulo,
                subtitulo=subtitulo,
                latitude=latitude,
                longitude=longitude,
                urgencia=urgencia,
                emergencia=emergencia,
                verificada=verificada,
                distancia_km=distancia,
                distancia_formatada=formatar_distancia(distancia),
            )
        )

    # --- Pins de solicitações (quem precisa de ajuda) ----------------------
    if TipoPontoMapa.AJUDA in tipos_desejados:
        solicitacoes = session.exec(
            select(Solicitacao).where(Solicitacao.status != StatusSolicitacao.CONCLUIDA)
        ).all()
        for solicitacao in solicitacoes:
            categoria = categorias.get(solicitacao.categoria_id)
            adicionar(
                id_=solicitacao.id,  # type: ignore[arg-type]
                tipo=TipoPontoMapa.AJUDA,
                titulo=solicitacao.titulo,
                subtitulo=(
                    f"{categoria.nome if categoria else 'Ajuda'} · "
                    f"{solicitacao.pessoas_beneficiadas} pessoa(s)"
                ),
                latitude=solicitacao.latitude,
                longitude=solicitacao.longitude,
                urgencia=solicitacao.urgencia.value,
                emergencia=solicitacao.emergencia,
            )

    # --- Pins de ofertas -------------------------------------------------- #
    # Uma oferta do tipo "ponto de retirada" vira um pin de categoria própria,
    # com ícone e filtro distintos das demais ofertas.
    quer_ofertas = TipoPontoMapa.OFERECENDO in tipos_desejados
    quer_retiradas = TipoPontoMapa.PONTO_RETIRADA in tipos_desejados
    if quer_ofertas or quer_retiradas:
        ofertas = session.exec(
            select(Oferta).where(Oferta.status == StatusOferta.DISPONIVEL)
        ).all()
        for oferta in ofertas:
            eh_retirada = oferta.tipo_ajuda == TipoAjuda.PONTO_RETIRADA
            tipo_pin = TipoPontoMapa.PONTO_RETIRADA if eh_retirada else TipoPontoMapa.OFERECENDO
            if tipo_pin not in tipos_desejados:
                continue
            categoria = categorias.get(oferta.categoria_id)
            adicionar(
                id_=oferta.id,  # type: ignore[arg-type]
                tipo=tipo_pin,
                titulo=oferta.titulo,
                subtitulo=(
                    f"{categoria.nome if categoria else 'Doação'} · "
                    f"{oferta.tipo_ajuda.value.replace('_', ' ')}"
                ),
                latitude=oferta.latitude,
                longitude=oferta.longitude,
            )

    # --- Pins de ONGs ------------------------------------------------------
    if TipoPontoMapa.ONG in tipos_desejados:
        for ong in session.exec(select(ONG)).all():
            adicionar(
                id_=ong.id,  # type: ignore[arg-type]
                tipo=TipoPontoMapa.ONG,
                titulo=ong.nome,
                subtitulo=f"{ong.avaliacao:.1f} ★ · {ong.total_avaliacoes} avaliações",
                latitude=ong.latitude,
                longitude=ong.longitude,
                verificada=ong.verificada,
            )

    if raio_km is not None:
        pontos = [
            p for p in pontos if p.distancia_km is not None and p.distancia_km <= raio_km
        ]

    # Emergências primeiro; no restante, do mais próximo ao mais distante.
    pontos.sort(key=lambda p: (not p.emergencia, chave_ordenacao_distancia(p.distancia_km)))

    total_por_tipo: dict[str, int] = {tipo.value: 0 for tipo in TipoPontoMapa}
    for ponto in pontos:
        total_por_tipo[ponto.tipo.value] += 1

    return RespostaMapa(pontos=pontos, total_por_tipo=total_por_tipo)
