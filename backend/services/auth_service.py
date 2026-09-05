"""
Serviço de autenticação.

Concentra as duas responsabilidades de segurança da aplicação:

1. **Senhas** — nunca são armazenadas em texto puro. Usamos `passlib` com o
   algoritmo *bcrypt*, que aplica salt automático e é propositalmente lento,
   dificultando ataques de força bruta.
2. **Tokens JWT** — após o login o cliente recebe um token assinado (HS256) que
   carrega o `id` do usuário no campo `sub`. Cada requisição protegida envia
   esse token no header `Authorization: Bearer <token>`.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.config import settings

# O bcrypt trunca a senha em 72 bytes; validamos esse limite nos schemas.
LIMITE_BYTES_SENHA = 72

# `deprecated="auto"` permite migrar de algoritmo no futuro sem quebrar hashes
# já gravados no banco.
contexto_senha = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --------------------------------------------------------------------------- #
# Senhas
# --------------------------------------------------------------------------- #
def gerar_hash_senha(senha: str) -> str:
    """Gera o hash bcrypt de uma senha em texto puro."""
    return contexto_senha.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    """Compara a senha informada no login com o hash armazenado."""
    try:
        return contexto_senha.verify(senha, senha_hash)
    except ValueError:
        # Hash corrompido ou em formato desconhecido: tratamos como senha inválida.
        return False


# --------------------------------------------------------------------------- #
# JWT
# --------------------------------------------------------------------------- #
def criar_access_token(
    usuario_id: int,
    expira_em_minutos: int | None = None,
    dados_extras: dict[str, Any] | None = None,
) -> str:
    """Cria um JWT assinado contendo o id do usuário.

    Args:
        usuario_id: identificador que vai no claim `sub`.
        expira_em_minutos: sobrescreve o tempo padrão vindo das configurações.
        dados_extras: claims adicionais (ex.: `{"tipo": "doador"}`).

    Returns:
        O token JWT codificado.
    """
    minutos = expira_em_minutos or settings.access_token_expire_minutes
    expiracao = datetime.now(timezone.utc) + timedelta(minutes=minutos)

    payload: dict[str, Any] = {
        "sub": str(usuario_id),   # a especificação do JWT exige `sub` como string
        "exp": expiracao,
        "iat": datetime.now(timezone.utc),
    }
    if dados_extras:
        payload.update(dados_extras)

    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decodificar_access_token(token: str) -> int | None:
    """Valida a assinatura/expiração do token e devolve o id do usuário.

    Retorna `None` quando o token é inválido, expirado ou não traz um `sub`
    numérico — cabe ao chamador transformar isso em um HTTP 401.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None

    sub = payload.get("sub")
    if sub is None:
        return None
    try:
        return int(sub)
    except (TypeError, ValueError):
        return None
