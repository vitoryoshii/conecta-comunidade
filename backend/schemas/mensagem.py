"""Schemas de mensagens e de listagem de conversas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MensagemCriar(BaseModel):
    """Payload de `POST /mensagens`."""

    destinatario_id: int
    texto: str = Field(min_length=1, max_length=2000)
    solicitacao_id: int | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "destinatario_id": 2,
                "texto": "Boa tarde! Consigo entregar amanhã às 14h.",
                "solicitacao_id": 1,
            }
        }
    )


class MensagemLer(BaseModel):
    """Mensagem individual exibida como bolha no chat."""

    id: int
    remetente_id: int
    destinatario_id: int
    solicitacao_id: int | None
    texto: str
    criada_em: datetime
    lida: bool

    # Nome do remetente, para o cabeçalho e para as bolhas.
    remetente_nome: str = ""

    model_config = ConfigDict(from_attributes=True)


class ConversaLer(BaseModel):
    """Resumo de uma conversa, usado na aba "Mensagens" da navegação inferior."""

    interlocutor_id: int
    interlocutor_nome: str
    interlocutor_avatar: str | None = None
    solicitacao_id: int | None = None
    solicitacao_titulo: str | None = None
    ultima_mensagem: str
    ultima_em: datetime
    nao_lidas: int = 0

    model_config = ConfigDict(from_attributes=True)
