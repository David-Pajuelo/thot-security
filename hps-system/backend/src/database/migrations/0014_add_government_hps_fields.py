"""add_government_hps_fields

Revision ID: 0014
Revises: 0013
Create Date: 2025-01-10 12:00:00.000000

Añade campos para integración con PDFs del gobierno y Excel histórico
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0014'
down_revision = '0013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Añadir campos para automatización de HPS del gobierno"""
    
    # Campos principales para datos del gobierno y Excel
    op.add_column('hps_requests', sa.Column('security_clearance_level', sa.String(255), nullable=True))
    op.add_column('hps_requests', sa.Column('government_expediente', sa.String(50), nullable=True))
    op.add_column('hps_requests', sa.Column('company_name', sa.String(255), nullable=True))
    op.add_column('hps_requests', sa.Column('company_nif', sa.String(20), nullable=True))
    op.add_column('hps_requests', sa.Column('internal_code', sa.String(50), nullable=True))
    op.add_column('hps_requests', sa.Column('job_position', sa.String(100), nullable=True))
    
    # Campos para trazabilidad de procesamiento automático
    op.add_column('hps_requests', sa.Column('auto_processed', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('hps_requests', sa.Column('source_pdf_filename', sa.String(255), nullable=True))
    op.add_column('hps_requests', sa.Column('auto_processed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('hps_requests', sa.Column('government_document_type', sa.String(100), nullable=True))
    
    # Campos adicionales para compatibilidad con Excel
    op.add_column('hps_requests', sa.Column('data_source', sa.String(50), nullable=True, server_default='manual'))  # manual, excel_import, pdf_auto
    op.add_column('hps_requests', sa.Column('original_status_text', sa.String(100), nullable=True))  # "en vigor (concedida)"
    
    # Índices para mejorar rendimiento
    op.create_index('idx_hps_requests_security_clearance', 'hps_requests', ['security_clearance_level'])
    op.create_index('idx_hps_requests_government_expediente', 'hps_requests', ['government_expediente'])
    op.create_index('idx_hps_requests_company_nif', 'hps_requests', ['company_nif'])
    op.create_index('idx_hps_requests_internal_code', 'hps_requests', ['internal_code'])
    op.create_index('idx_hps_requests_auto_processed', 'hps_requests', ['auto_processed'])
    op.create_index('idx_hps_requests_data_source', 'hps_requests', ['data_source'])


def downgrade() -> None:
    """Revertir cambios"""
    
    # Eliminar índices
    op.drop_index('idx_hps_requests_data_source', table_name='hps_requests')
    op.drop_index('idx_hps_requests_auto_processed', table_name='hps_requests')
    op.drop_index('idx_hps_requests_internal_code', table_name='hps_requests')
    op.drop_index('idx_hps_requests_company_nif', table_name='hps_requests')
    op.drop_index('idx_hps_requests_government_expediente', table_name='hps_requests')
    op.drop_index('idx_hps_requests_security_clearance', table_name='hps_requests')
    
    # Eliminar columnas
    op.drop_column('hps_requests', 'original_status_text')
    op.drop_column('hps_requests', 'data_source')
    op.drop_column('hps_requests', 'government_document_type')
    op.drop_column('hps_requests', 'auto_processed_at')
    op.drop_column('hps_requests', 'source_pdf_filename')
    op.drop_column('hps_requests', 'auto_processed')
    op.drop_column('hps_requests', 'job_position')
    op.drop_column('hps_requests', 'internal_code')
    op.drop_column('hps_requests', 'company_nif')
    op.drop_column('hps_requests', 'company_name')
    op.drop_column('hps_requests', 'government_expediente')
    op.drop_column('hps_requests', 'security_clearance_level')
