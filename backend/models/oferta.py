"""Modelo de Oferta — a proposta de quem quer ajudar."""

from datetime import datetime

from sqlmodel import Field, SQLModel

from backend.models.enums import StatusOferta, TipoAjuda
from backend.models.usuario import agora_utc


class Oferta(SQLModel, table=True):
    """Oferta de ajuda publicada por um doador ou voluntário.

    Quando criada a partir da tela "Quero ajudar", `solicitacao_id` aponta para
    o pedido que originou a proposta — é o que permite abrir o chat em seguida.
    """

    __tablename__ = "oferta"

    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True)

    titulo: str = Field(index=True, max_length=160)
    descricao: str = Field(default="", max_length=3000)
    categoria_id: int = Field(foreign_key="categoria.id", index=True)

    tipo_ajuda: TipoAjuda = Field(default=TipoAjuda.TENHO_ITEM, index=True)
    status: StatusOferta = Field(default=StatusOferta.DISPONIVEL, index=True)

    # Vínculo opcional com a solicitação que a oferta pretende atender.
    solicitacao_id: int | None = Field(default=None, foreign_key="solicitacao.id", index=True)

    latitude: float = Field(default=0.0)
    longitude: float = Field(default=0.0)
    endereco: str = Field(default="", max_length=300)

    criada_em: datetime = Field(default_factory=agora_utc, index=True)
