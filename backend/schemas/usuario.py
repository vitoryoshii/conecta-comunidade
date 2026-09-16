"""Schemas de autenticação e de usuário."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.models.enums import TipoUsuario


class UsuarioCriar(BaseModel):
    """Payload de `POST /auth/register`."""

    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    # 72 é o limite de bytes do bcrypt — validar aqui evita erro no hash.
    senha: str = Field(min_length=6, max_length=72)
    # Aceitos com ou sem máscara: o router normaliza para só dígitos antes de
    # gravar, e valida dígito verificador, DDD e idade mínima (422 se falhar).
    cpf: str = Field(min_length=11, max_length=14)
    telefone: str = Field(min_length=10, max_length=15)
    data_nascimento: date
    tipo: TipoUsuario = TipoUsuario.SOLICITANTE
    # Sigla da UF e nome do município; o router valida que a cidade pertence ao
    # estado antes de gravar (422 quando não pertence).
    estado: str = Field(default="", max_length=2)
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
                "cpf": "529.982.247-25",
                "telefone": "(11) 98765-4321",
                "data_nascimento": "1995-04-12",
                "tipo": "solicitante",
                "estado": "SP",
                "cidade": "São Paulo",
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
    """Representação **pública** de um usuário.

    É o que `GET /usuarios/{id}` devolve — o perfil que qualquer pessoa logada
    vê no chat e no detalhe de uma solicitação. Por isso não tem senha, CPF,
    telefone nem data de nascimento: acrescentar qualquer um deles aqui vaza o
    dado para toda a plataforma. Dados pessoais vivem em `UsuarioPrivadoLer`.
    """

    id: int
    nome: str
    email: EmailStr
    tipo: TipoUsuario
    estado: str
    cidade: str
    latitude: float
    longitude: float
    avatar_url: str | None = None
    criado_em: datetime
    solicitacoes_atendidas: int
    doacoes_recebidas: int
    acoes_voluntario: int

    model_config = ConfigDict(from_attributes=True)


class UsuarioPrivadoLer(UsuarioLer):
    """Retrato que **só o próprio dono** recebe (`GET /auth/me`).

    O CPF sai mascarado (`***.456.789-**`) mesmo aqui: dá para o usuário
    reconhecer o próprio número, mas não para reconstruí-lo caso a resposta
    acabe em um log ou no cache de alguém.
    """

    cpf: str | None = None
    telefone: str = ""
    data_nascimento: date | None = None


class UsuarioAtualizar(BaseModel):
    """Campos editáveis do perfil (`PATCH /usuarios/me`)."""

    nome: str | None = Field(default=None, min_length=2, max_length=120)
    estado: str | None = Field(default=None, max_length=2)
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
