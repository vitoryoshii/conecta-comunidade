"""Modelos SQLModel da aplicação.

Reexporta todas as entidades para que um único `import backend.models` já
registre o metadata completo (necessário para `create_all` e para o Alembic).
"""

from backend.models.categoria import Categoria
from backend.models.entrega import Entrega
from backend.models.enums import (
    StatusEntrega,
    StatusOferta,
    StatusSolicitacao,
    TipoAjuda,
    TipoPontoMapa,
    TipoUsuario,
    Urgencia,
)
from backend.models.mensagem import Mensagem
from backend.models.oferta import Oferta
from backend.models.ong import ONG
from backend.models.solicitacao import Solicitacao
from backend.models.usuario import Usuario, agora_utc

__all__ = [
    "Categoria",
    "Entrega",
    "Mensagem",
    "ONG",
    "Oferta",
    "Solicitacao",
    "Usuario",
    "StatusEntrega",
    "StatusOferta",
    "StatusSolicitacao",
    "TipoAjuda",
    "TipoPontoMapa",
    "TipoUsuario",
    "Urgencia",
    "agora_utc",
]
