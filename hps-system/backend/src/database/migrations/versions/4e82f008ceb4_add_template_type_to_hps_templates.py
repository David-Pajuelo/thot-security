"""add_template_type_to_hps_templates

Revision ID: 4e82f008ceb4
Revises: 3289eb4eac14
Create Date: 2025-11-13 11:56:25.932892

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4e82f008ceb4'
down_revision = '3289eb4eac14'
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
