from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.database import Base


class HpsTemplate(Base):
    __tablename__ = "hps_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    template_pdf = Column(LargeBinary, nullable=False)
    template_type = Column(String(50), nullable=False, default='jefe_seguridad', server_default='jefe_seguridad', index=True)  # 'jefe_seguridad' o 'jefe_seguridad_suplente'
    version = Column(String(50), nullable=False, default='1.0')
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    hps_requests = relationship("HPSRequest", back_populates="template")
    
    def __repr__(self):
        return f"<HpsTemplate(id={self.id}, name='{self.name}', template_type='{self.template_type}', version='{self.version}', active={self.active})>"
