"""Routers da API, agrupados por área do domínio."""

from backend.routers import (
    auth,
    categorias,
    entregas,
    favoritos,
    localidades,
    mapa,
    mensagens,
    ofertas,
    ongs,
    solicitacoes,
    usuarios,
)

__all__ = [
    "auth",
    "categorias",
    "entregas",
    "favoritos",
    "localidades",
    "mapa",
    "mensagens",
    "ofertas",
    "ongs",
    "solicitacoes",
    "usuarios",
]
