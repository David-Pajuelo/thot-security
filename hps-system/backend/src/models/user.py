from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.database import Base
import uuid

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    permissions = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    is_temp_password = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    role = relationship("Role", back_populates="users")
    team = relationship("Team", back_populates="members", foreign_keys=[team_id])
    team_lead = relationship("Team", back_populates="team_lead_user", foreign_keys="Team.team_lead_id")
    hps_requests = relationship("HPSRequest", back_populates="user", foreign_keys="HPSRequest.user_id")
    submitted_hps = relationship("HPSRequest", back_populates="submitted_by_user", foreign_keys="HPSRequest.submitted_by")
    approved_hps = relationship("HPSRequest", back_populates="approved_by_user", foreign_keys="HPSRequest.approved_by")
    requested_hps_tokens = relationship("HPSToken", back_populates="requested_by_user")
    audit_logs = relationship("AuditLog", back_populates="user")
    chat_conversations = relationship("ChatConversation", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def has_permission(self, permission):
        """Verificar si el usuario tiene un permiso específico"""
        if self.role.name == "admin":
            return True
        return self.role.permissions.get(permission, False)
