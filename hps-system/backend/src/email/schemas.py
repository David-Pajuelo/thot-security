"""
Schemas para el módulo de Email
Define los modelos Pydantic para correos electrónicos
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class EmailStatus(str, Enum):
    """Estados de un correo electrónico"""
    PENDING = "pending"           # Pendiente de envío
    SENT = "sent"                 # Enviado exitosamente
    FAILED = "failed"             # Error al enviar
    RECEIVED = "received"         # Recibido
    PROCESSED = "processed"       # Procesado por el agente


class EmailTemplate(str, Enum):
    """Templates de correos disponibles"""
    CONFIRMATION = "confirmation"         # Confirmación de solicitud
    STATUS_UPDATE = "status_update"       # Actualización de estado
    REMINDER = "reminder"                 # Recordatorio
    AUTO_REPLY = "auto_reply"            # Respuesta automática
    NOTIFICATION = "notification"        # Notificación general
    HPS_FORM = "hps_form"                # Formulario HPS
    USER_CREDENTIALS = "user_credentials" # Credenciales de usuario
    HPS_APPROVED = "hps_approved"        # HPS aprobada
    HPS_REJECTED = "hps_rejected"        # HPS rechazada
    NEW_USER_NOTIFICATION = "new_user_notification"  # Notificación de nuevo usuario
    HPS_EXPIRATION_REMINDER = "hps_expiration_reminder"  # Recordatorio de caducidad HPS


class EmailMessage(BaseModel):
    """Modelo para un mensaje de correo"""
    to: EmailStr = Field(..., description="Destinatario del correo")
    subject: str = Field(..., description="Asunto del correo")
    body: str = Field(..., description="Cuerpo del correo")
    html_body: Optional[str] = Field(None, description="Cuerpo HTML del correo")
    from_name: Optional[str] = Field(None, description="Nombre del remitente")
    reply_to: Optional[EmailStr] = Field(None, description="Email de respuesta")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Adjuntos")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EmailLog(BaseModel):
    """Modelo para el log de correos"""
    id: Optional[int] = None
    message_id: str = Field(..., description="ID único del mensaje")
    to: EmailStr = Field(..., description="Destinatario")
    from_email: EmailStr = Field(..., description="Remitente")
    subject: str = Field(..., description="Asunto")
    status: EmailStatus = Field(..., description="Estado del correo")
    template_used: Optional[EmailTemplate] = Field(None, description="Template utilizado")
    hps_request_id: Optional[int] = Field(None, description="ID de solicitud HPS relacionada")
    sent_at: Optional[datetime] = Field(None, description="Fecha de envío")
    received_at: Optional[datetime] = Field(None, description="Fecha de recepción")
    error_message: Optional[str] = Field(None, description="Mensaje de error si falló")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EmailTemplateData(BaseModel):
    """Datos para renderizar templates de correo"""
    user_name: str = Field(..., description="Nombre del usuario")
    user_email: EmailStr = Field(..., description="Email del usuario")
    recipient_name: Optional[str] = Field(None, description="Nombre del destinatario")
    recipient_email: Optional[EmailStr] = Field(None, description="Email del destinatario")
    hps_request_id: Optional[int] = Field(None, description="ID de solicitud HPS")
    document_number: Optional[str] = Field(None, description="Número de documento")
    request_type: Optional[str] = Field(None, description="Tipo de solicitud")
    status: Optional[str] = Field(None, description="Estado de la solicitud")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Datos adicionales")


class SendEmailRequest(BaseModel):
    """Request para enviar un correo"""
    to: EmailStr = Field(..., description="Destinatario")
    template: EmailTemplate = Field(..., description="Template a usar")
    template_data: EmailTemplateData = Field(..., description="Datos para el template")
    custom_subject: Optional[str] = Field(None, description="Asunto personalizado")
    custom_body: Optional[str] = Field(None, description="Cuerpo personalizado")


class EmailResponse(BaseModel):
    """Response para operaciones de email"""
    success: bool = Field(..., description="Si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo")
    email_id: Optional[str] = Field(None, description="ID del correo")
    error: Optional[str] = Field(None, description="Error si hubo alguno")


class ReceivedEmail(BaseModel):
    """Modelo para correos recibidos"""
    message_id: str = Field(..., description="ID del mensaje")
    from_email: EmailStr = Field(..., description="Remitente")
    subject: str = Field(..., description="Asunto")
    body: str = Field(..., description="Cuerpo del mensaje")
    received_at: datetime = Field(..., description="Fecha de recepción")
    is_read: bool = Field(False, description="Si ya fue leído")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Adjuntos")
