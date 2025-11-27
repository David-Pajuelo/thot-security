"""
Módulo de Email para HPS System
Maneja envío y recepción de correos electrónicos via Gmail
"""

from .smtp_client import SMTPClient
from .imap_client import IMAPClient
from .service import EmailService
from .schemas import EmailMessage, EmailTemplate, EmailStatus

__all__ = [
    "SMTPClient",
    "IMAPClient", 
    "EmailService",
    "EmailMessage",
    "EmailTemplate",
    "EmailStatus"
]
