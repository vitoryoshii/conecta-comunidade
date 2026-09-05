"""Modelo de Mensagem — conversas entre dois usuários."""

from datetime import datetime

from sqlmodel import Field, SQLModel

from backend.models.usuario import agora_utc


class Mensagem(SQLModel, table=True):
    """Mensagem trocada em um chat 1:1.

    O par (`remetente_id`, `destinatario_id`) identifica a conversa; quando a
    conversa nasce de um pedido específico, `solicitacao_id` mantém o contexto
    exibido no cabeçalho do chat.
    """

    __tablename__ = "mensagem"

    id: int | None = Field(default=None, primary_key=True)
    remetente_id: int = Field(foreign_key="usuario.id", index=True)
    destinatario_id: int = Field(foreign_key="usuario.id", index=True)
    solicitacao_id: int | None = Field(default=None, foreign_key="solicitacao.id", index=True)

    texto: str = Field(max_length=2000)
    criada_em: datetime = Field(default_factory=agora_utc, index=True)
    lida: bool = Field(default=False)
