from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.database import Base
import uuid

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    team_lead_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    members = relationship("User", back_populates="team", foreign_keys="User.team_id")
    team_lead_user = relationship("User", back_populates="team_lead", foreign_keys=[team_lead_id])
    
    @property
    def member_count(self):
        """Retorna el número de miembros activos en el equipo"""
        return len([member for member in self.members if member.is_active])
    
    def is_team_lead(self, user_id):
        """Verifica si un usuario es el líder del equipo"""
        return str(self.team_lead_id) == str(user_id)
