"""Update admin password

Revision ID: 0002
Revises: 0001
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Actualizar el password del usuario admin con un hash real
    # Password: admin123 (hash bcrypt generado con salt rounds 12)
    op.execute("""
        UPDATE users 
        SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK8i'
        WHERE email = 'admin@hps-system.com' 
        AND password_hash = 'placeholder_hash_change_in_production';
    """)


def downgrade() -> None:
    # Revertir a la contraseña placeholder
    op.execute("""
        UPDATE users 
        SET password_hash = 'placeholder_hash_change_in_production'
        WHERE email = 'admin@hps-system.com';
    """)
