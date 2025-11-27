"""Add AICOX default team

Revision ID: 0004
Revises: 0003
Create Date: 2024-12-01 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Insertar equipo AICOX por defecto si no existe
    op.execute("""
        INSERT INTO teams (id, name, description, is_active, created_at, updated_at) VALUES
        ('d8574c01-851f-4716-9ac9-bbda45469bdf', 'AICOX', 'Equipo genérico para usuarios sin equipo específico', true, now(), now())
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    # Eliminar el equipo AICOX
    op.execute("""
        DELETE FROM teams WHERE id = 'd8574c01-851f-4716-9ac9-bbda45469bdf'
    """)

