"""Add template_type to hps_templates

Revision ID: 0017_add_template_type
Revises: 0016_add_jefe_seguridad_suplente_role
Create Date: 2025-01-15 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0017_add_template_type'
down_revision = '0016_add_jefe_seguridad_suplente_role'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agregar columna template_type a hps_templates
    op.add_column('hps_templates', sa.Column('template_type', sa.String(50), nullable=False, server_default='jefe_seguridad'))
    
    # Crear índice para mejorar búsquedas
    op.create_index('idx_hps_templates_template_type', 'hps_templates', ['template_type'])
    
    # Actualizar plantillas existentes para que sean de tipo jefe_seguridad
    op.execute("""
        UPDATE hps_templates 
        SET template_type = 'jefe_seguridad' 
        WHERE template_type IS NULL OR template_type = ''
    """)


def downgrade() -> None:
    # Eliminar índice
    op.drop_index('idx_hps_templates_template_type', table_name='hps_templates')
    
    # Eliminar columna
    op.drop_column('hps_templates', 'template_type')

