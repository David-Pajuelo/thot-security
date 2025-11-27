"""add_conversation_data_json_field

Revision ID: 0009_add_conversation_data_json
Revises: 0008_add_chat_monitoring_tables
Create Date: 2025-09-05 09:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0009_add_conversation_data_json'
down_revision = '0008_add_chat_monitoring_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Agregar campo conversation_data JSON a chat_conversations
    op.add_column('chat_conversations', sa.Column('conversation_data', sa.JSON(), nullable=True))


def downgrade():
    # Eliminar campo conversation_data
    op.drop_column('chat_conversations', 'conversation_data')





