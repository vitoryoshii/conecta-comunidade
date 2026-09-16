"""Modelo de Usuário — pessoa física ou representante de instituição."""

from datetime import date, datetime, timezone

from sqlmodel import Field, SQLModel

from backend.models.enums import TipoUsuario


def agora_utc() -> datetime:
    """Data/hora atual em UTC (usada como default dos campos `criado_em`)."""
    return datetime.now(timezone.utc)


class Usuario(SQLModel, table=True):
    """Pessoa cadastrada na plataforma.

    Guarda também os três contadores exibidos na seção "Meu impacto" do perfil,
    mantidos de forma denormalizada para leitura rápida na tela inicial.
    """

    __tablename__ = "usuario"

    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(index=True, max_length=120)
    email: str = Field(unique=True, index=True, max_length=180)
    senha_hash: str = Field(max_length=255)
    tipo: TipoUsuario = Field(default=TipoUsuario.SOLICITANTE, index=True)

    # --- Dados pessoais ----------------------------------------------------
    # Guardados apenas com dígitos (sem máscara). O CPF é `None` para os
    # cadastros anteriores à exigência do campo — daí ser anulável apesar de
    # único: o índice aceita vários NULL, mas nenhum número repetido.
    #
    # Nenhum destes três campos aparece em `UsuarioLer`, o schema do perfil
    # público; só o próprio dono os recebe, e o CPF ainda vai mascarado.
    cpf: str | None = Field(default=None, unique=True, index=True, max_length=11)
    telefone: str = Field(default="", max_length=11)
    data_nascimento: date | None = Field(default=None)

    # Localização usada no cálculo de distância (haversine). `estado` guarda a
    # sigla da UF e `cidade` o nome oficial do município no IBGE — separados,
    # para permitir filtrar por UF sem precisar interpretar texto livre.
    estado: str = Field(default="", max_length=2, index=True)
    cidade: str = Field(default="", max_length=120)
    latitude: float = Field(default=0.0)
    longitude: float = Field(default=0.0)

    avatar_url: str | None = Field(default=None, max_length=500)
    criado_em: datetime = Field(default_factory=agora_utc)

    # --- Contadores de impacto (seção "Meu impacto") -----------------------
    solicitacoes_atendidas: int = Field(default=0)
    doacoes_recebidas: int = Field(default=0)
    acoes_voluntario: int = Field(default=0)
