"""
Configurações da aplicação Conecta Comunidade.

Todas as variáveis sensíveis (segredo do JWT, URL do banco) são lidas de
variáveis de ambiente ou do arquivo `.env` na raiz do projeto, de forma que
nenhum segredo precise ser versionado no repositório.
"""

from functools import lru_cache
from os import getenv
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Raiz do projeto (diretório que contém `backend/`, `mobile/`, `.env` ...)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Configurações tipadas e validadas pelo Pydantic v2."""

    # --- Identidade da API -------------------------------------------------
    app_nome: str = "Conecta Comunidade API"
    app_versao: str = "1.0.0"
    debug: bool = True

    # --- Banco de dados ----------------------------------------------------
    # SQLite por padrão (desenvolvimento). Para PostgreSQL basta exportar:
    #   DATABASE_URL=postgresql+psycopg://usuario:senha@host:5432/conecta
    database_url: str = f"sqlite:///{BASE_DIR / 'conecta.db'}"

    # --- Segurança / JWT ---------------------------------------------------
    secret_key: str = "troque-esta-chave-em-producao-conecta-comunidade"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 dias

    # --- CORS --------------------------------------------------------------
    # "*" facilita a apresentação acadêmica; em produção liste os domínios.
    cors_origins: str = "*"

    # --- Integração mobile -------------------------------------------------
    # URL que o app Flet usa para falar com a API.
    api_base_url: str = "http://127.0.0.1:8000"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validar_segredo_de_producao(self) -> "Settings":
        """Recusa o segredo padrão ou fraco no runtime de produção da Vercel."""
        ambiente_vercel = getenv("VERCEL_ENV", "").strip().lower()
        segredo_padrao = "troque-esta-chave-em-producao-conecta-comunidade"
        if ambiente_vercel == "production" and (
            self.secret_key == segredo_padrao or len(self.secret_key.strip()) < 32
        ):
            raise ValueError(
                "SECRET_KEY deve estar configurada e ter ao menos 32 caracteres em Production."
            )
        return self

    @property
    def lista_cors_origins(self) -> list[str]:
        """Converte a string de origens (separadas por vírgula) em lista."""
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origem.strip() for origem in self.cors_origins.split(",") if origem.strip()]

    @property
    def is_sqlite(self) -> bool:
        """Indica se o banco configurado é SQLite (muda alguns parâmetros do engine)."""
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Retorna a instância única de configurações (cacheada)."""
    return Settings()


# Instância global usada pelos módulos da aplicação.
settings = get_settings()
