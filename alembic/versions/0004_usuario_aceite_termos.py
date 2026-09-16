"""usuario: aceite dos termos e data do consentimento

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-16

Registra o consentimento exigido pela LGPD. As duas colunas nascem com
`server_default` para que as contas já existentes continuem válidas: elas ficam
com `aceite_termos = 0` e `data_aceite = NULL`, o que é a verdade — ninguém
aceitou nada antes de o app pedir. Inventar um aceite retroativo seria pior do
que não ter registro.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# Identificadores da revisão, usados pelo Alembic.
revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aplica a migration."""
    with op.batch_alter_table('usuario', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('aceite_termos', sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.add_column(sa.Column('data_aceite', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Desfaz a migration."""
    with op.batch_alter_table('usuario', schema=None) as batch_op:
        batch_op.drop_column('data_aceite')
        batch_op.drop_column('aceite_termos')
