"""Modelo de Favorito — solicitações que o usuário guardou para depois."""

from datetime import datetime

from sqlmodel import Field, SQLModel, UniqueConstraint

from backend.models.usuario import agora_utc


class Favorito(SQLModel, table=True):
    """Marcação de uma solicitação como favorita por um usuário.

    É uma tabela de ligação: guarda o par (usuário, solicitação) e quando ele
    foi criado. A restrição única no par é o que torna "favoritar" idempotente
    no banco — tocar duas vezes no coração não cria duas linhas, mesmo que dois
    toques cheguem juntos.
    """

    __tablename__ = "favorito"
    __table_args__ = (
        UniqueConstraint("usuario_id", "solicitacao_id", name="uq_favorito_usuario_solicitacao"),
    )

    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True)
    solicitacao_id: int = Field(foreign_key="solicitacao.id", index=True)
    criado_em: datetime = Field(default_factory=agora_utc)
