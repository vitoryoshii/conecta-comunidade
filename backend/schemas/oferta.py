"""Schemas de oferta (propostas de quem quer ajudar)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.models.enums import StatusOferta, TipoAjuda


class OfertaCriar(BaseModel):
    """Payload de `POST /ofertas`.

    Quando enviado a partir da tela "Quero ajudar", `solicitacao_id` aponta para
    o pedido atendido e `mensagem` (opcional) já cria a primeira mensagem do
    chat com o solicitante.
    """

    titulo: str = Field(min_length=3, max_length=160)
    descricao: str = Field(default="", max_length=3000)
    categoria_id: int
    tipo_ajuda: TipoAjuda = TipoAjuda.TENHO_ITEM
    solicitacao_id: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    endereco: str = Field(default="", max_length=300)
    mensagem: str | None = Field(default=None, max_length=2000)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "titulo": "Tenho 30 litros de água mineral",
                "descricao": "Posso separar hoje ainda.",
                "categoria_id": 1,
                "tipo_ajuda": "tenho_item",
                "solicitacao_id": 1,
                "mensagem": "Olá! Consigo levar hoje à tarde, pode ser?",
            }
        }
    )


class OfertaLer(BaseModel):
    """Oferta enriquecida com dados de exibição."""

    id: int
    usuario_id: int
    titulo: str
    descricao: str
    categoria_id: int
    tipo_ajuda: TipoAjuda
    status: StatusOferta
    solicitacao_id: int | None
    latitude: float
    longitude: float
    endereco: str
    criada_em: datetime

    # --- Campos derivados --------------------------------------------------
    categoria_nome: str = ""
    categoria_icone: str = "category"
    autor_nome: str = ""
    autor_avatar: str | None = None
    distancia_km: float | None = None
    distancia_formatada: str = "--"
    tempo_publicacao: str = ""

    model_config = ConfigDict(from_attributes=True)
