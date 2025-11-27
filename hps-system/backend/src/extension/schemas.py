# Esquemas para el complemento de navegador
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

class PersonaListResponse(BaseModel):
    """Respuesta para lista de personas"""
    tipo_documento: str
    numero_documento: str
    fecha_nacimiento: Optional[date] = None
    nombre: str
    primer_apellido: str
    segundo_apellido: str
    nacionalidad: Optional[str] = None
    lugar_nacimiento: Optional[str] = None
    correo: Optional[EmailStr] = None
    telefono: Optional[str] = None
    operacion: Optional[str] = None

class PersonaDetailResponse(BaseModel):
    """Respuesta para datos detallados de una persona"""
    tipo_documento: str
    numero_documento: str
    fecha_nacimiento: Optional[date] = None
    nombre: str
    primer_apellido: str
    segundo_apellido: str
    nacionalidad: Optional[str] = None
    lugar_nacimiento: Optional[str] = None
    correo: Optional[EmailStr] = None
    telefono: Optional[str] = None
    operacion: Optional[str] = None
    estado: str

class UpdateEstadoRequest(BaseModel):
    """Request para actualizar estado de solicitud"""
    estado: str

class UpdateEstadoResponse(BaseModel):
    """Respuesta para actualización de estado"""
    success: bool
    message: str

