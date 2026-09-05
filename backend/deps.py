"""
Dependências reutilizáveis do FastAPI.

Reúne o fornecimento da sessão de banco e a resolução do usuário autenticado a
partir do token JWT. Rotas de escrita usam `UsuarioAtual`; rotas de leitura que
funcionam também para visitantes usam `UsuarioOpcional`.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from backend.database import get_session
from backend.models import Usuario
from backend.services.auth_service import decodificar_access_token

# `auto_error=False` permite que o mesmo esquema atenda rotas públicas, nas
# quais a ausência do header não deve gerar erro automático.
esquema_bearer = HTTPBearer(auto_error=False, description="Token JWT obtido em /auth/login")

SessionDep = Annotated[Session, Depends(get_session)]
CredenciaisDep = Annotated[HTTPAuthorizationCredentials | None, Depends(esquema_bearer)]


def _usuario_do_token(credenciais: HTTPAuthorizationCredentials | None, session: Session) -> Usuario | None:
    """Resolve o usuário a partir do header Authorization, ou `None`."""
    if credenciais is None or not credenciais.credentials:
        return None

    usuario_id = decodificar_access_token(credenciais.credentials)
    if usuario_id is None:
        return None

    return session.get(Usuario, usuario_id)


def get_current_user(credenciais: CredenciaisDep, session: SessionDep) -> Usuario:
    """Exige um token JWT válido e devolve o usuário correspondente.

    Raises:
        HTTPException 401: token ausente, inválido, expirado ou usuário removido.
    """
    usuario = _usuario_do_token(credenciais, session)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas ou expiradas. Faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario


def get_current_user_optional(credenciais: CredenciaisDep, session: SessionDep) -> Usuario | None:
    """Versão tolerante: devolve o usuário logado ou `None` (modo visitante)."""
    return _usuario_do_token(credenciais, session)


# Aliases usados nas assinaturas dos routers, deixando-as mais legíveis.
UsuarioAtual = Annotated[Usuario, Depends(get_current_user)]
UsuarioOpcional = Annotated[Usuario | None, Depends(get_current_user_optional)]
