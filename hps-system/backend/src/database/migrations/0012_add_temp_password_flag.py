"""Add is_temp_password flag to users table

Revision ID: 0012
Revises: 0011
Create Date: 2024-12-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agregar columna is_temp_password a la tabla users
    op.add_column('users', sa.Column('is_temp_password', sa.Boolean(), nullable=True, default=False))
    
    # Actualizar todos los usuarios existentes para que no tengan contraseña temporal
    op.execute("UPDATE users SET is_temp_password = false WHERE is_temp_password IS NULL")


def downgrade() -> None:
    # Eliminar columna is_temp_password
    op.drop_column('users', 'is_temp_password')
