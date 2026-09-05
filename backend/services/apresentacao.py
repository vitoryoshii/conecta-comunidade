"""
Serviço de apresentação.

Converte as entidades do banco nos schemas de leitura que o app consome,
acrescentando os campos derivados que não existem nas tabelas: nome da
categoria, nome do autor, distância em relação ao usuário e o "tempo desde a
publicação" exibido nos cards.

Manter essa montagem em um único lugar evita repetir a mesma lógica em cada
router e garante que Home, Explorar e Mapa mostrem exatamente os mesmos números.
"""

from datetime import datetime, timezone

from sqlmodel import Session, select

from backend.models import Categoria, Oferta, Solicitacao, Usuario
from backend.schemas.oferta import OfertaLer
from backend.schemas.solicitacao import SolicitacaoLer
from backend.services.geo_service import calcular_distancia_km, formatar_distancia


def _como_utc(momento: datetime) -> datetime:
    """Normaliza datas para UTC.

    O SQLite devolve datetimes "ingênuos" (sem fuso); assumimos UTC nesses casos
    para que a subtração com `datetime.now(timezone.utc)` não gere TypeError.
    """
    if momento.tzinfo is None:
        return momento.replace(tzinfo=timezone.utc)
    return momento.astimezone(timezone.utc)


def tempo_desde(momento: datetime) -> str:
    """Texto amigável de tempo decorrido ("há 2 h", "há 3 d", "agora")."""
    delta = datetime.now(timezone.utc) - _como_utc(momento)
    segundos = int(delta.total_seconds())

    if segundos < 60:
        return "agora"
    if segundos < 3600:
        return f"há {segundos // 60} min"
    if segundos < 86_400:
        return f"há {segundos // 3600} h"
    dias = segundos // 86_400
    if dias < 30:
        return f"há {dias} d"
    meses = dias // 30
    if meses < 12:
        return f"há {meses} mês" if meses == 1 else f"há {meses} meses"
    return f"há {meses // 12} ano(s)"


def carregar_mapa_categorias(session: Session) -> dict[int, Categoria]:
    """Carrega todas as categorias em memória (são poucas) indexadas por id."""
    return {c.id: c for c in session.exec(select(Categoria)).all() if c.id is not None}


def carregar_mapa_usuarios(session: Session, ids: set[int]) -> dict[int, Usuario]:
    """Carrega em lote os autores citados numa listagem, evitando N+1 queries."""
    if not ids:
        return {}
    usuarios = session.exec(select(Usuario).where(Usuario.id.in_(ids))).all()  # type: ignore[attr-defined]
    return {u.id: u for u in usuarios if u.id is not None}


def montar_solicitacao(
    solicitacao: Solicitacao,
    categorias: dict[int, Categoria],
    usuarios: dict[int, Usuario],
    origem_lat: float | None = None,
    origem_lon: float | None = None,
) -> SolicitacaoLer:
    """Converte uma `Solicitacao` no schema de leitura enriquecido."""
    categoria = categorias.get(solicitacao.categoria_id)
    autor = usuarios.get(solicitacao.usuario_id)

    distancia = calcular_distancia_km(
        origem_lat, origem_lon, solicitacao.latitude, solicitacao.longitude
    )

    return SolicitacaoLer(
        **solicitacao.model_dump(),
        categoria_nome=categoria.nome if categoria else "",
        categoria_icone=categoria.icone if categoria else "category",
        autor_nome=autor.nome if autor else "",
        autor_avatar=autor.avatar_url if autor else None,
        distancia_km=distancia,
        distancia_formatada=formatar_distancia(distancia),
        tempo_publicacao=tempo_desde(solicitacao.criada_em),
    )


def montar_oferta(
    oferta: Oferta,
    categorias: dict[int, Categoria],
    usuarios: dict[int, Usuario],
    origem_lat: float | None = None,
    origem_lon: float | None = None,
) -> OfertaLer:
    """Converte uma `Oferta` no schema de leitura enriquecido."""
    categoria = categorias.get(oferta.categoria_id)
    autor = usuarios.get(oferta.usuario_id)

    distancia = calcular_distancia_km(origem_lat, origem_lon, oferta.latitude, oferta.longitude)

    return OfertaLer(
        **oferta.model_dump(),
        categoria_nome=categoria.nome if categoria else "",
        categoria_icone=categoria.icone if categoria else "category",
        autor_nome=autor.nome if autor else "",
        autor_avatar=autor.avatar_url if autor else None,
        distancia_km=distancia,
        distancia_formatada=formatar_distancia(distancia),
        tempo_publicacao=tempo_desde(oferta.criada_em),
    )
