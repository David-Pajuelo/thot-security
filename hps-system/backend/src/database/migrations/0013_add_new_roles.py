"""Add new roles: jefe_seguridad and crypto

Revision ID: 0013
Revises: 0012
Create Date: 2025-01-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0013'
down_revision = '0012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Insertar nuevos roles en la tabla roles
    op.execute("""
        INSERT INTO roles (name, description, created_at, updated_at) 
        VALUES 
        ('jefe_seguridad', 'Jefe de Seguridad', NOW(), NOW()),
        ('crypto', 'Crypto', NOW(), NOW())
        ON CONFLICT (name) DO NOTHING
    """)


def downgrade() -> None:
    # Eliminar los nuevos roles
    op.execute("DELETE FROM roles WHERE name IN ('jefe_seguridad', 'crypto')")

