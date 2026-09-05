"""
Camada de acesso ao banco de dados.

Centraliza a criação do engine SQLAlchemy/SQLModel, a fábrica de sessões e a
rotina de criação das tabelas (`init_db`). O mesmo módulo atende SQLite (dev) e
PostgreSQL (produção), bastando trocar a variável `DATABASE_URL`.
"""

from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from backend.config import settings

# `check_same_thread=False` é necessário porque o SQLite, por padrão, recusa
# conexões vindas de threads diferentes — e o Uvicorn atende requisições em
# múltiplas threads.
connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

engine = create_engine(
    settings.database_url,
    echo=False,          # ligue para ver o SQL gerado durante a depuração
    connect_args=connect_args,
)


def init_db() -> None:
    """Cria todas as tabelas mapeadas pelos modelos SQLModel.

    Em produção o versionamento do schema é feito pelo Alembic; esta função
    existe para facilitar o desenvolvimento e a demonstração acadêmica.
    """
    # O import garante que todos os modelos estejam registrados no metadata
    # antes do `create_all`.
    import backend.models  # noqa: F401  (efeito colateral proposital)

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependência do FastAPI que fornece uma sessão por requisição."""
    with Session(engine) as session:
        yield session
