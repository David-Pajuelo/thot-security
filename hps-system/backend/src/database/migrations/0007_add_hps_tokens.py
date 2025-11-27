"""Add HPS tokens table

Revision ID: 0007
Revises: 0005
Create Date: 2024-12-19 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Crear tabla hps_tokens para tokens seguros"""
    
    # Crear tabla hps_tokens
    op.create_table('hps_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('purpose', sa.String(length=500), nullable=True),
        sa.Column('is_used', sa.Boolean(), nullable=False, default=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['requested_by'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('token')
    )
    
    # Crear índices para optimizar consultas
    op.create_index('ix_hps_tokens_token', 'hps_tokens', ['token'])
    op.create_index('ix_hps_tokens_email', 'hps_tokens', ['email'])
    op.create_index('ix_hps_tokens_requested_by', 'hps_tokens', ['requested_by'])
    op.create_index('ix_hps_tokens_expires_at', 'hps_tokens', ['expires_at'])
    op.create_index('ix_hps_tokens_is_used', 'hps_tokens', ['is_used'])


def downgrade() -> None:
    """Eliminar tabla hps_tokens"""
    
    # Eliminar índices
    op.drop_index('ix_hps_tokens_is_used', table_name='hps_tokens')
    op.drop_index('ix_hps_tokens_expires_at', table_name='hps_tokens')
    op.drop_index('ix_hps_tokens_requested_by', table_name='hps_tokens')
    op.drop_index('ix_hps_tokens_email', table_name='hps_tokens')
    op.drop_index('ix_hps_tokens_token', table_name='hps_tokens')
    
    # Eliminar tabla
    op.drop_table('hps_tokens')
