from sqlalchemy import Column, String, Date, DateTime, Text, ForeignKey, Integer, LargeBinary, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.database import Base
import uuid
import enum

class HPSType(enum.Enum):
    SOLICITUD = "solicitud"
    TRASLADO = "traslado"

class HPSRequest(Base):
    __tablename__ = "hps_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    request_type = Column(String(50), nullable=False, index=True)  # 'new', 'renewal', 'transfer'
    status = Column(String(50), default='pending', index=True)  # 'pending', 'approved', 'rejected', 'expired'
    
    # Campos para traslados
    type = Column(String(20), nullable=False, default='solicitud', index=True)
    template_id = Column(Integer, ForeignKey("hps_templates.id"), nullable=True)
    filled_pdf = Column(LargeBinary, nullable=True)
    response_pdf = Column(LargeBinary, nullable=True)
    
    # Datos personales del formulario
    document_type = Column(String(50), nullable=False)
    document_number = Column(String(50), nullable=False)
    birth_date = Column(Date, nullable=False)
    first_name = Column(String(100), nullable=False)
    first_last_name = Column(String(100), nullable=False)
    second_last_name = Column(String(100), nullable=True)
    nationality = Column(String(100), nullable=False)
    birth_place = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    
    # Metadatos
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Campos para integración con PDFs del gobierno y Excel histórico
    security_clearance_level = Column(String(255), nullable=True)  # Grado y especialidad (R,NS, UE-S, ESA-S)
    government_expediente = Column(String(50), nullable=True, index=True)  # Número expediente gobierno (E-25-027334)
    company_name = Column(String(255), nullable=True)  # Empresa/Organismo
    company_nif = Column(String(20), nullable=True, index=True)  # NIF/CIF empresa
    internal_code = Column(String(50), nullable=True)  # Código interno AICOX (045D)
    job_position = Column(String(100), nullable=True)  # Cargo/Puesto
    
    # Campos para trazabilidad de procesamiento automático
    auto_processed = Column(Boolean, default=False, nullable=True)  # Procesado automáticamente desde PDF
    source_pdf_filename = Column(String(255), nullable=True)  # Archivo PDF origen del gobierno
    auto_processed_at = Column(DateTime(timezone=True), nullable=True)  # Fecha procesamiento automático
    government_document_type = Column(String(100), nullable=True)  # Tipo documento gobierno
    data_source = Column(String(50), default='manual', nullable=True)  # manual, excel_import, pdf_auto
    original_status_text = Column(String(100), nullable=True)  # Estado original del Excel/PDF
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="hps_requests", foreign_keys=[user_id])
    submitted_by_user = relationship("User", back_populates="submitted_hps", foreign_keys=[submitted_by])
    approved_by_user = relationship("User", back_populates="approved_hps", foreign_keys=[approved_by])
    template = relationship("HpsTemplate", back_populates="hps_requests")
    
    @property
    def is_expired(self):
        """Verifica si la solicitud HPS ha expirado"""
        if not self.expires_at:
            return False
        from datetime import date
        return self.expires_at < date.today()
    
    @property
    def can_be_approved(self):
        """Verifica si la solicitud puede ser aprobada"""
        return self.status == 'pending' and not self.is_expired
    
    def approve(self, approved_by_user_id, expires_at=None):
        """Aprueba la solicitud HPS"""
        self.status = 'approved'
        self.approved_by = approved_by_user_id
        self.approved_at = func.now()
        if expires_at:
            self.expires_at = expires_at
    
    def reject(self, approved_by_user_id, notes=None):
        """Rechaza la solicitud HPS"""
        self.status = 'rejected'
        self.approved_by = approved_by_user_id
        self.approved_at = func.now()
        if notes:
            self.notes = notes
