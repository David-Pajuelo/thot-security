"""add_hps_templates_table

Revision ID: 0010_add_hps_templates
Revises: 0009_add_conversation_data_json
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0010_add_hps_templates'
down_revision = '0009_add_conversation_data_json'
branch_labels = None
depends_on = None


def upgrade():
    # Crear tabla hps_templates
    op.create_table('hps_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_pdf', sa.LargeBinary(), nullable=False),
        sa.Column('version', sa.String(50), nullable=False, default='1.0'),
        sa.Column('active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Eliminar tabla hps_templates
    op.drop_table('hps_templates')

