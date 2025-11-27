"""Add waiting_dps status to HPS requests

Revision ID: 0015_add_waiting_dps_status
Revises: 0014_add_government_hps_fields
Create Date: 2025-01-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0015_add_waiting_dps_status'
down_revision = '0014_add_government_hps_fields'
branch_labels = None
depends_on = None


def upgrade():
    """Add waiting_dps status to HPS requests"""
    # No need to modify the enum in PostgreSQL as it's handled by the application
    # The waiting_dps status is already defined in the schemas
    pass


def downgrade():
    """Remove waiting_dps status"""
    # No need to modify the enum in PostgreSQL
    pass
