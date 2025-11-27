"""Initial schema migration

Revision ID: 0001
Revises: 
Create Date: 2024-12-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Crear extensión para UUID
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Crear tabla roles
    op.create_table('roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)
    
    # Crear tabla teams
    op.create_table('teams',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('team_lead_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Crear tabla users
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('email_verified', sa.Boolean(), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_role'), 'users', ['role_id'], unique=False)
    op.create_index(op.f('ix_users_team'), 'users', ['team_id'], unique=False)
    
    # Crear tabla hps_requests
    op.create_table('hps_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('document_number', sa.String(length=50), nullable=False),
        sa.Column('birth_date', sa.Date(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('first_last_name', sa.String(length=100), nullable=False),
        sa.Column('second_last_name', sa.String(length=100), nullable=True),
        sa.Column('nationality', sa.String(length=100), nullable=False),
        sa.Column('birth_place', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=False),
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hps_requests_user'), 'hps_requests', ['user_id'], unique=False)
    op.create_index(op.f('ix_hps_requests_status'), 'hps_requests', ['status'], unique=False)
    op.create_index(op.f('ix_hps_requests_type'), 'hps_requests', ['request_type'], unique=False)
    
    # Crear tabla audit_logs
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('table_name', sa.String(length=100), nullable=True),
        sa.Column('record_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_user'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_created'), 'audit_logs', ['created_at'], unique=False)
    
    # Crear foreign keys
    op.create_foreign_key('fk_users_role', 'users', 'roles', ['role_id'], ['id'])
    op.create_foreign_key('fk_users_team', 'users', 'teams', ['team_id'], ['id'])
    op.create_foreign_key('fk_teams_lead', 'teams', 'users', ['team_lead_id'], ['id'])
    op.create_foreign_key('fk_hps_user', 'hps_requests', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_hps_submitted', 'hps_requests', 'users', ['submitted_by'], ['id'])
    op.create_foreign_key('fk_hps_approved', 'hps_requests', 'users', ['approved_by'], ['id'])
    op.create_foreign_key('fk_audit_user', 'audit_logs', 'users', ['user_id'], ['id'])
    
    # Insertar equipo AICOX por defecto
    op.execute("""
        INSERT INTO teams (id, name, description, is_active) VALUES
        ('d8574c01-851f-4716-9ac9-bbda45469bdf', 'AICOX', 'Equipo genérico para usuarios sin equipo específico', true)
        ON CONFLICT (id) DO NOTHING
    """)
    
    # Insertar roles básicos
    op.execute("""
        INSERT INTO roles (name, description, permissions) VALUES
        ('admin', 'Administrador del sistema con acceso completo', '{"all": true}'),
        ('team_lead', 'Jefe de equipo con permisos de gestión de equipo', '{"team_management": true, "hps_requests": true, "user_view": true}'),
        ('member', 'Miembro del equipo con acceso básico', '{"hps_view": true, "profile_edit": true}')
        ON CONFLICT (name) DO NOTHING
    """)
    
    # Insertar usuario administrador por defecto
    op.execute("""
        INSERT INTO users (email, password_hash, first_name, last_name, role_id) VALUES
        ('admin@hps-system.com', 'placeholder_hash_change_in_production', 'Admin', 'Sistema', 1)
        ON CONFLICT (email) DO NOTHING
    """)


def downgrade() -> None:
    # Eliminar foreign keys
    op.drop_constraint('fk_audit_user', 'audit_logs', type_='foreignkey')
    op.drop_constraint('fk_hps_approved', 'hps_requests', type_='foreignkey')
    op.drop_constraint('fk_hps_submitted', 'hps_requests', type_='foreignkey')
    op.drop_constraint('fk_hps_user', 'hps_requests', type_='foreignkey')
    op.drop_constraint('fk_teams_lead', 'teams', type_='foreignkey')
    op.drop_constraint('fk_users_team', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_role', 'users', type_='foreignkey')
    
    # Eliminar tablas
    op.drop_table('audit_logs')
    op.drop_table('hps_requests')
    op.drop_table('users')
    op.drop_table('teams')
    op.drop_table('roles')
