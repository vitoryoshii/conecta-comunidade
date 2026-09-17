"""favoritos e preferências de notificação

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-17

Cria a tabela de favoritos e as três preferências de notificação do usuário.
As preferências nascem ligadas (`server_default='1'`) porque é o que as contas
existentes esperariam: quem nunca abriu Configurações continua sendo avisado.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# Identificadores da revisão, usados pelo Alembic.
revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aplica a migration."""
    op.create_table(
        'favorito',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('solicitacao_id', sa.Integer(), nullable=False),
        sa.Column('criado_em', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['solicitacao_id'], ['solicitacao.id']),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id']),
        sa.PrimaryKeyConstraint('id'),
        # O par é único: é o que faz favoritar duas vezes não criar duas linhas.
        sa.UniqueConstraint(
            'usuario_id', 'solicitacao_id', name='uq_favorito_usuario_solicitacao'
        ),
    )
    op.create_index(op.f('ix_favorito_usuario_id'), 'favorito', ['usuario_id'])
    op.create_index(op.f('ix_favorito_solicitacao_id'), 'favorito', ['solicitacao_id'])

    with op.batch_alter_table('usuario', schema=None) as batch_op:
        for coluna in (
            'notificar_solicitacoes',
            'notificar_mensagens',
            'notificar_atualizacoes',
        ):
            batch_op.add_column(
                sa.Column(coluna, sa.Boolean(), nullable=False, server_default=sa.true())
            )


def downgrade() -> None:
    """Desfaz a migration."""
    with op.batch_alter_table('usuario', schema=None) as batch_op:
        batch_op.drop_column('notificar_atualizacoes')
        batch_op.drop_column('notificar_mensagens')
        batch_op.drop_column('notificar_solicitacoes')

    op.drop_index(op.f('ix_favorito_solicitacao_id'), table_name='favorito')
    op.drop_index(op.f('ix_favorito_usuario_id'), table_name='favorito')
    op.drop_table('favorito')
