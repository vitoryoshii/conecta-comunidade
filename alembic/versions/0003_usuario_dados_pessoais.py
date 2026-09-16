"""usuario: cpf, telefone e data de nascimento

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-16

Acrescenta os dados pessoais exigidos no cadastro. O CPF é anulável de
propósito: os cadastros já existentes não têm o número, e um índice único
aceita vários NULL — o que preserva a unicidade sem inventar valor para quem
se cadastrou antes.
"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# Identificadores da revisão, usados pelo Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aplica a migration."""
    with op.batch_alter_table('usuario', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('cpf', sqlmodel.sql.sqltypes.AutoString(length=11), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                'telefone',
                sqlmodel.sql.sqltypes.AutoString(length=11),
                nullable=False,
                server_default='',
            )
        )
        batch_op.add_column(sa.Column('data_nascimento', sa.Date(), nullable=True))
        batch_op.create_index(batch_op.f('ix_usuario_cpf'), ['cpf'], unique=True)


def downgrade() -> None:
    """Desfaz a migration."""
    with op.batch_alter_table('usuario', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_usuario_cpf'))
        batch_op.drop_column('data_nascimento')
        batch_op.drop_column('telefone')
        batch_op.drop_column('cpf')
