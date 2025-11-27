"""add_hps_transfer_fields

Revision ID: 0011_add_hps_transfer_fields
Revises: 0010_add_hps_templates
Create Date: 2025-01-27 10:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0011_add_hps_transfer_fields'
down_revision = '0010_add_hps_templates'
branch_labels = None
depends_on = None


def upgrade():
    # Agregar campos para traslados a tabla hps_requests
    op.add_column('hps_requests', sa.Column('type', sa.Enum('solicitud', 'traslado', name='hps_type'), nullable=False, default='solicitud'))
    op.add_column('hps_requests', sa.Column('template_id', sa.Integer(), nullable=True))
    op.add_column('hps_requests', sa.Column('filled_pdf', sa.LargeBinary(), nullable=True))
    op.add_column('hps_requests', sa.Column('response_pdf', sa.LargeBinary(), nullable=True))
    
    # Crear foreign key constraint
    op.create_foreign_key('fk_hps_requests_template', 'hps_requests', 'hps_templates', ['template_id'], ['id'])


def downgrade():
    # Eliminar foreign key constraint
    op.drop_constraint('fk_hps_requests_template', 'hps_requests', type_='foreignkey')
    
    # Eliminar campos
    op.drop_column('hps_requests', 'response_pdf')
    op.drop_column('hps_requests', 'filled_pdf')
    op.drop_column('hps_requests', 'template_id')
    op.drop_column('hps_requests', 'type')
    
    # Eliminar enum type
    op.execute('DROP TYPE hps_type')
