"""usuario.estado

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-15

Acrescenta a sigla da UF ao usuário. Até aqui a localização vivia só no campo
livre `cidade` ("Vila Madalena - São Paulo/SP"); com o cadastro passando a usar
a base do IBGE, a UF ganha coluna própria e `cidade` passa a guardar apenas o
nome oficial do município.
"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# Identificadores da revisão, usados pelo Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aplica a migration."""
    with op.batch_alter_table('usuario', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'estado',
                sqlmodel.sql.sqltypes.AutoString(length=2),
                nullable=False,
                server_default='',
            )
        )
        batch_op.create_index(batch_op.f('ix_usuario_estado'), ['estado'], unique=False)


def downgrade() -> None:
    """Desfaz a migration."""
    with op.batch_alter_table('usuario', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_usuario_estado'))
        batch_op.drop_column('estado')
