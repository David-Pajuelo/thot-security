"""Update existing HPS data to new codes

Revision ID: 0006
Revises: 0005
Create Date: 2024-12-20 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Update existing HPS data to use new codes"""
    
    # Mapping for document types
    document_type_mapping = {
        'DNI': '206',
        'NIE': '207', 
        'PASSPORT': '209',
        # Add any other old values that might exist
    }
    
    # Mapping for nationality (common old values to new codes)
    nationality_mapping = {
        'Española': '1',
        'España': '1',
        'Spanish': '1',
        'Española ': '1',  # With trailing space
        'ESPAÑOLA': '1',
        'SPAIN': '1',
        # Add other common variations if they exist
    }
    
    # Update document_type
    for old_value, new_value in document_type_mapping.items():
        op.execute(
            f"UPDATE hps_requests SET document_type = '{new_value}' WHERE document_type = '{old_value}'"
        )
    
    # Update nationality  
    for old_value, new_value in nationality_mapping.items():
        op.execute(
            f"UPDATE hps_requests SET nationality = '{new_value}' WHERE nationality = '{old_value}'"
        )
    
    # Handle any remaining unmapped nationalities - set them to "2" (DESCONOCIDO)
    # First, get all unique nationality values that are not already numeric codes
    conn = op.get_bind()
    result = conn.execute(
        "SELECT DISTINCT nationality FROM hps_requests WHERE nationality !~ '^[0-9]+$'"
    )
    
    for row in result:
        nationality = row[0]
        if nationality and nationality.strip():
            print(f"Warning: Unmapped nationality '{nationality}' set to DESCONOCIDO (2)")
            op.execute(
                f"UPDATE hps_requests SET nationality = '2' WHERE nationality = '{nationality}'"
            )

def downgrade() -> None:
    """Revert HPS data to old format"""
    
    # Reverse mapping for document types
    reverse_document_mapping = {
        '206': 'DNI',
        '207': 'NIE', 
        '208': 'TARJETA_RESIDENTE',
        '209': 'PASSPORT',
        '210': 'OTROS'
    }
    
    # Update document_type back
    for new_value, old_value in reverse_document_mapping.items():
        op.execute(
            f"UPDATE hps_requests SET document_type = '{old_value}' WHERE document_type = '{new_value}'"
        )
    
    # For nationality, we'll just set everything back to "Española" since we can't perfectly reverse
    op.execute("UPDATE hps_requests SET nationality = 'Española'")










