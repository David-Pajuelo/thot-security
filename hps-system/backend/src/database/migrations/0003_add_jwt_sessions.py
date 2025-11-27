"""Add JWT sessions table

Revision ID: 0003
Revises: 0002
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Crear tabla de sesiones JWT compatible con UUIDs
    op.create_table('user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Crear índices para optimizar consultas de sesiones
    op.create_index('idx_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('idx_user_sessions_token_hash', 'user_sessions', ['token_hash'])
    op.create_index('idx_user_sessions_expires_at', 'user_sessions', ['expires_at'])
    op.create_index('idx_user_sessions_cleanup', 'user_sessions', ['expires_at', 'user_id'])


def downgrade() -> None:
    # Eliminar índices
    op.drop_index('idx_user_sessions_cleanup', 'user_sessions')
    op.drop_index('idx_user_sessions_expires_at', 'user_sessions')
    op.drop_index('idx_user_sessions_token_hash', 'user_sessions')
    op.drop_index('idx_user_sessions_user_id', 'user_sessions')
    
    # Eliminar tabla
    op.drop_table('user_sessions')
