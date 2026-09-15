"""Schemas de autenticação e de usuário."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.models.enums import TipoUsuario


class UsuarioCriar(BaseModel):
    """Payload de `POST /auth/register`."""

    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    # 72 é o limite de bytes do bcrypt — validar aqui evita erro no hash.
    senha: str = Field(min_length=6, max_length=72)
    tipo: TipoUsuario = TipoUsuario.SOLICITANTE
    cidade: str = Field(default="", max_length=120)
    latitude: float = 0.0
    longitude: float = 0.0
    avatar_url: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "Ana Ribeiro",
                "email": "ana@exemplo.com",
                "senha": "senha123",
                "tipo": "solicitante",
                "cidade": "São Paulo - SP",
                "latitude": -23.5505,
                "longitude": -46.6333,
            }
        }
    )


class UsuarioLogin(BaseModel):
    """Payload de `POST /auth/login`."""

    email: EmailStr
    senha: str

    model_config = ConfigDict(
        json_schema_extra={"example": {"email": "ana@exemplo.com", "senha": "senha123"}}
    )


class RecuperarSenha(BaseModel):
    """Payload de `POST /auth/recuperar-senha`."""

    email: EmailStr

    model_config = ConfigDict(json_schema_extra={"example": {"email": "ana@exemplo.com"}})


class RecuperarSenhaResposta(BaseModel):
    """Confirmação genérica do pedido de redefinição de senha."""

    mensagem: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"mensagem": "Se o e-mail existir, enviamos um link de redefinição."}
        }
    )


class UsuarioLer(BaseModel):
    """Representação pública de um usuário (nunca expõe o hash da senha)."""

    id: int
    nome: str
    email: EmailStr
    tipo: TipoUsuario
    cidade: str
    latitude: float
    longitude: float
    avatar_url: str | None = None
    criado_em: datetime
    solicitacoes_atendidas: int
    doacoes_recebidas: int
    acoes_voluntario: int

    model_config = ConfigDict(from_attributes=True)


class UsuarioAtualizar(BaseModel):
    """Campos editáveis do perfil (`PATCH /usuarios/me`)."""

    nome: str | None = Field(default=None, min_length=2, max_length=120)
    cidade: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    avatar_url: str | None = None


class Token(BaseModel):
    """Resposta do login: token JWT + dados do usuário autenticado."""

    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioLer

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "usuario": {"id": 1, "nome": "Ana Ribeiro", "email": "ana@exemplo.com"},
            }
        }
    )


class ImpactoLer(BaseModel):
    """Números exibidos na seção "Meu impacto" do perfil."""

    solicitacoes_atendidas: int
    doacoes_recebidas: int
    acoes_voluntario: int
    total_solicitacoes_criadas: int
    total_ofertas_criadas: int
    pessoas_beneficiadas: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "solicitacoes_atendidas": 3,
                "doacoes_recebidas": 7,
                "acoes_voluntario": 5,
                "total_solicitacoes_criadas": 4,
                "total_ofertas_criadas": 2,
                "pessoas_beneficiadas": 18,
            }
        }
    )
