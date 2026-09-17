"""
Camada de acesso ao banco de dados.

Centraliza a criação do engine SQLAlchemy/SQLModel e a fábrica de sessões. O
mesmo módulo atende SQLite (dev) e PostgreSQL (produção), bastando trocar a
variável `DATABASE_URL`.

O schema **não** é criado aqui: quem cria e versiona as tabelas é o Alembic
(`alembic upgrade head`). Manter uma segunda fonte de verdade (`create_all`)
fazia tabelas nascerem fora do controle das migrations e colidirem com elas na
próxima `alembic upgrade`.
"""

from collections.abc import Generator

from sqlmodel import Session, create_engine

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


def get_session() -> Generator[Session, None, None]:
    """Dependência do FastAPI que fornece uma sessão por requisição."""
    with Session(engine) as session:
        yield session
