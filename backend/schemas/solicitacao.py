"""Schemas de solicitação (pedidos de ajuda)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.models.enums import StatusSolicitacao, Urgencia


class SolicitacaoCriar(BaseModel):
    """Payload de `POST /solicitacoes`."""

    titulo: str = Field(min_length=3, max_length=160)
    descricao: str = Field(default="", max_length=3000)
    categoria_id: int
    quantidade: str = Field(default="", max_length=120)
    urgencia: Urgencia = Urgencia.MEDIA
    pessoas_beneficiadas: int = Field(default=1, ge=1)
    latitude: float | None = None
    longitude: float | None = None
    endereco: str = Field(default="", max_length=300)
    fotos: list[str] = Field(default_factory=list)
    emergencia: bool = False

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "titulo": "Água potável para 4 famílias",
                "descricao": "Falta de abastecimento há 3 dias na comunidade.",
                "categoria_id": 1,
                "quantidade": "50 litros",
                "urgencia": "alta",
                "pessoas_beneficiadas": 16,
                "latitude": -23.5610,
                "longitude": -46.6560,
                "endereco": "Rua das Acácias, 120 - São Paulo/SP",
                "emergencia": True,
            }
        }
    )


class SolicitacaoAtualizar(BaseModel):
    """Payload de `PATCH /solicitacoes/{id}` — todos os campos são opcionais."""

    titulo: str | None = Field(default=None, min_length=3, max_length=160)
    descricao: str | None = None
    categoria_id: int | None = None
    quantidade: str | None = None
    urgencia: Urgencia | None = None
    status: StatusSolicitacao | None = None
    pessoas_beneficiadas: int | None = Field(default=None, ge=1)
    latitude: float | None = None
    longitude: float | None = None
    endereco: str | None = None
    fotos: list[str] | None = None
    emergencia: bool | None = None

    model_config = ConfigDict(json_schema_extra={"example": {"status": "em_andamento"}})


class SolicitacaoLer(BaseModel):
    """Solicitação enriquecida com dados de exibição do app.

    Os campos `distancia_km`, `distancia_formatada` e `tempo_publicacao` são
    calculados no router — não existem na tabela.
    """

    id: int
    usuario_id: int
    titulo: str
    descricao: str
    categoria_id: int
    quantidade: str
    urgencia: Urgencia
    status: StatusSolicitacao
    pessoas_beneficiadas: int
    latitude: float
    longitude: float
    endereco: str
    fotos: list[str]
    emergencia: bool
    criada_em: datetime

    # --- Campos derivados (não persistidos) --------------------------------
    categoria_nome: str = ""
    categoria_icone: str = "category"
    autor_nome: str = ""
    autor_avatar: str | None = None
    distancia_km: float | None = None
    distancia_formatada: str = "--"
    tempo_publicacao: str = ""

    model_config = ConfigDict(from_attributes=True)
