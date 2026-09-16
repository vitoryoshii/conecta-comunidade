"""Schemas Pydantic v2 usados nas requisições e respostas da API."""

from backend.schemas.categoria import CategoriaLer
from backend.schemas.localidade import CidadeLer, EstadoLer
from backend.schemas.entrega import EntregaAtualizar, EntregaCriar, EntregaLer
from backend.schemas.mapa import PontoMapa, RespostaMapa
from backend.schemas.mensagem import ConversaLer, MensagemCriar, MensagemLer
from backend.schemas.oferta import OfertaCriar, OfertaLer
from backend.schemas.ong import AvaliacaoCriar, ONGLer
from backend.schemas.solicitacao import SolicitacaoAtualizar, SolicitacaoCriar, SolicitacaoLer
from backend.schemas.usuario import (
    ImpactoLer,
    RecuperarSenha,
    RecuperarSenhaResposta,
    Token,
    UsuarioAtualizar,
    UsuarioCriar,
    UsuarioLer,
    UsuarioLogin,
    UsuarioPrivadoLer,
)

__all__ = [
    "AvaliacaoCriar",
    "CategoriaLer",
    "CidadeLer",
    "ConversaLer",
    "EntregaAtualizar",
    "EntregaCriar",
    "EntregaLer",
    "EstadoLer",
    "ImpactoLer",
    "MensagemCriar",
    "MensagemLer",
    "ONGLer",
    "OfertaCriar",
    "OfertaLer",
    "PontoMapa",
    "RecuperarSenha",
    "RecuperarSenhaResposta",
    "RespostaMapa",
    "SolicitacaoAtualizar",
    "SolicitacaoCriar",
    "SolicitacaoLer",
    "Token",
    "UsuarioAtualizar",
    "UsuarioCriar",
    "UsuarioLer",
    "UsuarioLogin",
    "UsuarioPrivadoLer",
]
