"""Add new role: jefe_seguridad_suplente

Revision ID: 0016_add_jefe_seguridad_suplente
Revises: 0015_add_waiting_dps_status
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0016_add_jefe_seguridad_suplente'
down_revision = '0015_add_waiting_dps_status'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Insertar nuevo rol en la tabla roles
    op.execute("""
        INSERT INTO roles (name, description, created_at, updated_at) 
        VALUES 
        ('jefe_seguridad_suplente', 'Jefe de Seguridad Suplente', NOW(), NOW())
        ON CONFLICT (name) DO NOTHING
    """)


def downgrade() -> None:
    # Eliminar el nuevo rol
    op.execute("DELETE FROM roles WHERE name = 'jefe_seguridad_suplente'")

