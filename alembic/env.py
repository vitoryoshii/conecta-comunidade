"""
Ambiente de execução das migrations do Alembic.

Diferenças em relação ao arquivo gerado por `alembic init`:

* a URL do banco vem de `backend.config.settings` (portanto, da variável de
  ambiente `DATABASE_URL`), evitando duplicar a configuração no `alembic.ini`;
* o `target_metadata` aponta para o metadata do SQLModel, o que habilita o
  `alembic revision --autogenerate`;
* `render_as_batch` fica ligado para que o SQLite consiga executar alterações
  de coluna (ele não suporta `ALTER COLUMN` nativamente).
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

# Importar os modelos registra todas as tabelas no metadata do SQLModel.
import backend.models  # noqa: F401
from backend.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# A URL efetiva sempre vem das configurações da aplicação.
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Gera o SQL das migrations sem abrir conexão com o banco."""
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Aplica as migrations conectando de fato ao banco."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
