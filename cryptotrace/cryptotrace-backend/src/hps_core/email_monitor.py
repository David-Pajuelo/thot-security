"""
Monitor de correos HPS para automatización de estados en Django
Adaptado desde hps-system/backend/src/email/hps_monitor.py
Sistema de escucha y procesamiento automático de correos del gobierno
"""

import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone

from .imap_client import IMAPClient
from .email_service import HpsEmailService
from .models import HpsRequest
from .tasks import send_hps_status_update_email

logger = logging.getLogger(__name__)


class HPSEmailMonitor:
    """
    Monitor de correos para automatización de estados HPS
    Procesa correos del gobierno y actualiza estados automáticamente
    """
    
    def __init__(self, imap_client: Optional[IMAPClient] = None, email_service: Optional[HpsEmailService] = None):
        """
        Inicializa el monitor de correos HPS
        
        Args:
            imap_client: Cliente IMAP (opcional, se crea uno nuevo si no se proporciona)
            email_service: Servicio de email (opcional, se crea uno nuevo si no se proporciona)
        """
        self.imap_client = imap_client or IMAPClient()
        self.email_service = email_service or HpsEmailService()
        
        # Patrones de correos del gobierno
        self.government_senders = [
            "no-reply@ccn-cert.cni.es",
            "noreply@ccn-cert.cni.es", 
            "solicitudes@ccn-cert.cni.es",
            "hps@ccn-cert.cni.es"
        ]
        
        # Patrones de contenido para detectar cambios de estado
        self.status_patterns = {
            "waiting_dps": [
                r"ha sido enviada al interesado para su realización",
                r"se le ha enviado un formulario gubernamental",
                r"formulario DPS enviado",
                r"Nueva solicitud de Habilitación Personal de Seguridad"
            ],
            "submitted": [
                r"ha sido enviada a la entidad competente",
                r"enviada para su procesamiento",
                r"en trámite administrativo"
            ],
            "approved": [
                r"ha sido aprobada",
                r"habilitación concedida",
                r"procedimiento completado exitosamente",
                r"autorización otorgada"
            ],
            "rejected": [
                r"ha sido rechazada",
                r"solicitud denegada",
                r"no cumple los requisitos",
                r"procedimiento denegado"
            ],
            "expired": [
                r"ha expirado",
                r"vencimiento de la habilitación",
                r"plazo vencido"
            ]
        }
    
    def monitor_emails(self, since_days: int = 1) -> Dict[str, Any]:
        """
        Monitorea correos nuevos y procesa cambios de estado
        
        Args:
            since_days: Días hacia atrás para buscar correos
            
        Returns:
            Dict con resultados del procesamiento
        """
        try:
            logger.info("Iniciando monitorización de correos HPS...")
            
            # Obtener correos nuevos
            new_emails = self.imap_client.get_unread_emails(since_days)
            
            if not new_emails:
                logger.info("No se encontraron correos nuevos")
                return {
                    "success": True,
                    "emails_processed": 0,
                    "status_updates": 0,
                    "errors": []
                }
            
            # Procesar cada correo
            processed_count = 0
            status_updates = 0
            errors = []
            
            for email_data in new_emails:
                try:
                    # Verificar si es un correo del gobierno
                    if self._is_government_email(email_data):
                        logger.info(f"Procesando correo del gobierno: {email_data.get('subject', 'Sin asunto')}")
                        
                        # Procesar el correo y actualizar estados
                        result = self._process_government_email(email_data)
                        
                        if result["status_updated"]:
                            status_updates += 1
                            logger.info(f"Estado actualizado para HPS: {result['hps_id']}")
                        
                        processed_count += 1
                        
                        # Marcar como leído
                        message_id = email_data.get("message_id")
                        if message_id:
                            self.imap_client.mark_as_read(message_id)
                        
                except Exception as e:
                    error_msg = f"Error procesando correo {email_data.get('message_id', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            logger.info(f"Monitorización completada: {processed_count} correos procesados, {status_updates} estados actualizados")
            
            return {
                "success": True,
                "emails_processed": processed_count,
                "status_updates": status_updates,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error en monitorización de correos: {str(e)}")
            return {
                "success": False,
                "emails_processed": 0,
                "status_updates": 0,
                "errors": [str(e)]
            }
    
    def _is_government_email(self, email_data: Dict[str, Any]) -> bool:
        """
        Verifica si un correo es del gobierno
        
        Args:
            email_data: Diccionario con información del correo
            
        Returns:
            True si es un correo del gobierno
        """
        # Verificar remitente
        from_email = email_data.get("from_email", "").lower()
        for gov_sender in self.government_senders:
            if gov_sender.lower() in from_email:
                return True
        
        # Verificar asunto (patrones adicionales)
        subject = email_data.get("subject", "").lower()
        government_keywords = [
            "habilitación personal de seguridad",
            "hps",
            "ccn-cert",
            "solicitud",
            "formulario dps"
        ]
        
        for keyword in government_keywords:
            if keyword in subject:
                return True
        
        return False
    
    def _process_government_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un correo del gobierno y actualiza estados HPS
        
        Args:
            email_data: Diccionario con información del correo
            
        Returns:
            Dict con resultado del procesamiento
        """
        try:
            # Extraer información del correo
            email_info = self._extract_email_info(email_data)
            
            if not email_info["person_name"]:
                logger.warning(f"No se pudo extraer nombre de persona del correo: {email_data.get('subject', 'Sin asunto')}")
                return {"status_updated": False, "hps_id": None}
            
            # Buscar HPS correspondiente
            hps_request = self._find_matching_hps(email_info)
            
            if not hps_request:
                logger.warning(f"No se encontró HPS para: {email_info['person_name']}")
                return {"status_updated": False, "hps_id": None}
            
            # Determinar nuevo estado
            new_status = self._determine_new_status(email_data)
            
            if not new_status:
                logger.info(f"No se pudo determinar nuevo estado para HPS {hps_request.id}")
                return {"status_updated": False, "hps_id": hps_request.id}
            
            # Actualizar estado
            if hps_request.status != new_status:
                old_status = hps_request.status
                hps_request.status = new_status
                hps_request.updated_at = timezone.now()
                hps_request.save(update_fields=['status', 'updated_at'])
                
                logger.info(f"HPS {hps_request.id} actualizada: {old_status} -> {new_status}")
                
                # Enviar notificación de cambio de estado (incluyendo el correo original)
                self._send_status_notification(hps_request, old_status, new_status, email_data)
                
                return {"status_updated": True, "hps_id": hps_request.id}
            else:
                logger.info(f"HPS {hps_request.id} ya está en estado {new_status}")
                return {"status_updated": False, "hps_id": hps_request.id}
                
        except Exception as e:
            logger.error(f"Error procesando correo del gobierno: {str(e)}")
            return {"status_updated": False, "hps_id": None}
    
    def _extract_email_info(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae información relevante del correo
        
        IMPORTANTE: El destinatario del correo (ej: Ángel Bonacasa) NO es el solicitante.
        El solicitante es la persona mencionada en el CONTENIDO del correo.
        
        Args:
            email_data: Diccionario con información del correo
            
        Returns:
            Dict con información extraída del SOLICITANTE (no del destinatario)
        """
        info = {
            "person_name": None,        # Nombre del SOLICITANTE (del contenido)
            "document_number": None,    # Documento del SOLICITANTE
            "date": None,              # Fecha de la solicitud
            "recipient_email": email_data.get("to_email", ""),  # Email del destinatario (jefe de seguridad)
            "recipient_name": None     # Nombre del destinatario (jefe de seguridad)
        }
        
        # Buscar nombre del SOLICITANTE en el contenido (NO el destinatario)
        subject = email_data.get("subject", "")
        body = email_data.get("body", "")
        content = f"{subject} {body}"
        
        # Patrones para extraer nombre del SOLICITANTE (del contenido)
        name_patterns = [
            r"de\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+),\s+con\s+fecha",  # "de Laur Jiemnez, con fecha"
            r"([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+),\s+con\s+fecha\s+\d{2}/\d{2}/\d{4}",  # "Laur Jiemnez, con fecha 02/07/2025"
            r"de\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)",  # "de Juan Pérez"
            r"interesado\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)",  # "interesado Juan Pérez"
            r"([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+),\s+con\s+fecha",  # "Juan Pérez, con fecha"
            r"solicitud.*?de\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)",  # "solicitud de Juan Pérez"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                info["person_name"] = match.group(1).strip()
                logger.info(f"Nombre del SOLICITANTE extraído: {info['person_name']}")
                break
        
        # Buscar número de documento del SOLICITANTE
        doc_patterns = [
            r"DNI\s*:?\s*(\d{8}[A-Z])",
            r"NIE\s*:?\s*([A-Z]\d{7}[A-Z])",
            r"documento\s*:?\s*(\d{8}[A-Z]|[A-Z]\d{7}[A-Z])"
        ]
        
        for pattern in doc_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                info["document_number"] = match.group(1).strip()
                logger.info(f"Documento del SOLICITANTE extraído: {info['document_number']}")
                break
        
        # Buscar fecha
        date_patterns = [
            r"fecha\s+(\d{2}/\d{2}/\d{4})",
            r"(\d{2}/\d{2}/\d{4})"
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content)
            if match:
                info["date"] = match.group(1)
                break
        
        return info
    
    def _find_matching_hps(self, email_info: Dict[str, Any]) -> Optional[HpsRequest]:
        """
        Busca la HPS que coincide con la información del SOLICITANTE (no del destinatario)
        
        IMPORTANTE: Busca por el nombre del SOLICITANTE extraído del contenido,
        NO por el destinatario del correo (jefe de seguridad).
        
        Args:
            email_info: Información extraída del correo (del SOLICITANTE)
            
        Returns:
            HpsRequest que coincide o None
        """
        try:
            # Buscar por nombre completo del SOLICITANTE
            if email_info["person_name"]:
                name_parts = email_info["person_name"].split()
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = " ".join(name_parts[1:])
                    
                    logger.info(f"Buscando HPS para SOLICITANTE: {first_name} {last_name}")
                    
                    hps = HpsRequest.objects.filter(
                        first_name__icontains=first_name,
                        first_last_name__icontains=last_name,
                        status="pending"  # Solo buscar en estado pending
                    ).first()
                    
                    if hps:
                        logger.info(f"HPS encontrada para SOLICITANTE: {hps.id}")
                        return hps
            
            # Buscar por número de documento del SOLICITANTE
            if email_info["document_number"]:
                logger.info(f"Buscando HPS por documento del SOLICITANTE: {email_info['document_number']}")
                
                hps = HpsRequest.objects.filter(
                    document_number=email_info["document_number"],
                    status="pending"
                ).first()
                
                if hps:
                    logger.info(f"HPS encontrada por documento del SOLICITANTE: {hps.id}")
                    return hps
            
            return None
            
        except Exception as e:
            logger.error(f"Error buscando HPS coincidente: {str(e)}")
            return None
    
    def _determine_new_status(self, email_data: Dict[str, Any]) -> Optional[str]:
        """
        Determina el nuevo estado basado en el contenido del correo
        
        Args:
            email_data: Diccionario con información del correo
            
        Returns:
            Nuevo estado o None si no se puede determinar
        """
        subject = email_data.get("subject", "")
        body = email_data.get("body", "")
        content = f"{subject} {body}".lower()
        
        # Verificar cada patrón de estado
        for status, patterns in self.status_patterns.items():
            for pattern in patterns:
                if re.search(pattern.lower(), content):
                    logger.info(f"Detectado cambio a estado: {status}")
                    return status
        
        return None
    
    def _send_status_notification(self, hps_request: HpsRequest, old_status: str, new_status: str, original_email_data: Dict[str, Any]):
        """
        Envía notificación de cambio de estado incluyendo el correo original del gobierno
        
        Args:
            hps_request: Solicitud HPS actualizada
            old_status: Estado anterior
            new_status: Nuevo estado
            original_email_data: Diccionario con información del correo original del gobierno
        """
        try:
            # Obtener usuario
            user = hps_request.user
            
            if not user:
                logger.warning(f"Usuario no encontrado para HPS {hps_request.id}")
                return
            
            # Preparar datos adicionales con información del correo original
            additional_data = {
                "old_status": old_status,
                "original_email_from": original_email_data.get("from_email", ""),
                "original_email_subject": original_email_data.get("subject", ""),
                "original_email_body": original_email_data.get("body", ""),
                "original_email_date": original_email_data.get("received_at", "").strftime("%d/%m/%Y %H:%M:%S") if original_email_data.get("received_at") else ""
            }
            
            # Enviar email usando el servicio con información del correo original
            success = self.email_service.send_hps_status_update_email(
                hps_request=hps_request,
                new_status=new_status,
                old_status=old_status,
                additional_data=additional_data
            )
            
            if success:
                logger.info(f"Notificación de cambio de estado enviada para HPS {hps_request.id}")
            else:
                logger.error(f"Error enviando notificación de cambio de estado para HPS {hps_request.id}")
                
        except Exception as e:
            logger.error(f"Error enviando notificación de cambio de estado: {str(e)}")

