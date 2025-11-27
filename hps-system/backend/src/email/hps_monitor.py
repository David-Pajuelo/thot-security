"""
Monitor de correos HPS para automatización de estados
Sistema de escucha y procesamiento automático de correos del gobierno
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .service import EmailService
from ..models.hps import HPSRequest
from ..models.user import User
from ..database.database import get_db

logger = logging.getLogger(__name__)


class HPSEmailMonitor:
    """
    Monitor de correos para automatización de estados HPS
    Procesa correos del gobierno y actualiza estados automáticamente
    """
    
    def __init__(self, email_service: EmailService):
        self.email_service = email_service
        
        # Patrones de correos del gobierno (TEMPORALES - cambiar por credenciales definitivas)
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
    
    def monitor_emails(self, db: Session, since_days: int = 1) -> Dict[str, Any]:
        """
        Monitorea correos nuevos y procesa cambios de estado
        
        Args:
            db: Sesión de base de datos
            since_days: Días hacia atrás para buscar correos
            
        Returns:
            Dict con resultados del procesamiento
        """
        try:
            logger.info("Iniciando monitorización de correos HPS...")
            
            # Obtener correos nuevos
            new_emails = self.email_service.check_new_emails(since_days)
            
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
            
            for email in new_emails:
                try:
                    # Verificar si es un correo del gobierno
                    if self._is_government_email(email):
                        logger.info(f"Procesando correo del gobierno: {email.subject}")
                        
                        # Procesar el correo y actualizar estados
                        result = self._process_government_email(email, db)
                        
                        if result["status_updated"]:
                            status_updates += 1
                            logger.info(f"Estado actualizado para HPS: {result['hps_id']}")
                        
                        processed_count += 1
                        
                        # Marcar como leído
                        self.email_service.mark_email_as_read(email.message_id)
                        
                except Exception as e:
                    error_msg = f"Error procesando correo {email.message_id}: {str(e)}"
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
    
    def _is_government_email(self, email) -> bool:
        """
        Verifica si un correo es del gobierno
        
        Args:
            email: Objeto ReceivedEmail
            
        Returns:
            True si es un correo del gobierno
        """
        # Verificar remitente
        sender_lower = email.from_email.lower()
        for gov_sender in self.government_senders:
            if gov_sender.lower() in sender_lower:
                return True
        
        # Verificar asunto (patrones adicionales)
        subject_lower = email.subject.lower()
        government_keywords = [
            "habilitación personal de seguridad",
            "hps",
            "ccn-cert",
            "solicitud",
            "formulario dps"
        ]
        
        for keyword in government_keywords:
            if keyword in subject_lower:
                return True
        
        return False
    
    def _process_government_email(self, email, db: Session) -> Dict[str, Any]:
        """
        Procesa un correo del gobierno y actualiza estados HPS
        
        Args:
            email: Objeto ReceivedEmail
            db: Sesión de base de datos
            
        Returns:
            Dict con resultado del procesamiento
        """
        try:
            # Extraer información del correo
            email_info = self._extract_email_info(email)
            
            if not email_info["person_name"]:
                logger.warning(f"No se pudo extraer nombre de persona del correo: {email.subject}")
                return {"status_updated": False, "hps_id": None}
            
            # Buscar HPS correspondiente
            hps_request = self._find_matching_hps(email_info, db)
            
            if not hps_request:
                logger.warning(f"No se encontró HPS para: {email_info['person_name']}")
                return {"status_updated": False, "hps_id": None}
            
            # Determinar nuevo estado
            new_status = self._determine_new_status(email)
            
            if not new_status:
                logger.info(f"No se pudo determinar nuevo estado para HPS {hps_request.id}")
                return {"status_updated": False, "hps_id": hps_request.id}
            
            # Actualizar estado
            if hps_request.status != new_status:
                old_status = hps_request.status
                hps_request.status = new_status
                hps_request.updated_at = datetime.utcnow()
                
                db.commit()
                
                logger.info(f"HPS {hps_request.id} actualizada: {old_status} -> {new_status}")
                
                # Enviar notificación de cambio de estado (incluyendo el correo original)
                self._send_status_notification(hps_request, old_status, new_status, email, db)
                
                return {"status_updated": True, "hps_id": hps_request.id}
            else:
                logger.info(f"HPS {hps_request.id} ya está en estado {new_status}")
                return {"status_updated": False, "hps_id": hps_request.id}
                
        except Exception as e:
            logger.error(f"Error procesando correo del gobierno: {str(e)}")
            return {"status_updated": False, "hps_id": None}
    
    def _extract_email_info(self, email) -> Dict[str, Any]:
        """
        Extrae información relevante del correo
        
        IMPORTANTE: El destinatario del correo (ej: Ángel Bonacasa) NO es el solicitante.
        El solicitante es la persona mencionada en el CONTENIDO del correo.
        
        Args:
            email: Objeto ReceivedEmail
            
        Returns:
            Dict con información extraída del SOLICITANTE (no del destinatario)
        """
        info = {
            "person_name": None,        # Nombre del SOLICITANTE (del contenido)
            "document_number": None,    # Documento del SOLICITANTE
            "date": None,              # Fecha de la solicitud
            "recipient_email": email.from_email,  # Email del destinatario (jefe de seguridad)
            "recipient_name": None     # Nombre del destinatario (jefe de seguridad)
        }
        
        # Buscar nombre del SOLICITANTE en el contenido (NO el destinatario)
        content = f"{email.subject} {email.body}"
        
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
    
    def _find_matching_hps(self, email_info: Dict[str, Any], db: Session) -> Optional[HPSRequest]:
        """
        Busca la HPS que coincide con la información del SOLICITANTE (no del destinatario)
        
        IMPORTANTE: Busca por el nombre del SOLICITANTE extraído del contenido,
        NO por el destinatario del correo (jefe de seguridad).
        
        Args:
            email_info: Información extraída del correo (del SOLICITANTE)
            db: Sesión de base de datos
            
        Returns:
            HPSRequest que coincide o None
        """
        try:
            # Buscar por nombre completo del SOLICITANTE
            if email_info["person_name"]:
                name_parts = email_info["person_name"].split()
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = " ".join(name_parts[1:])
                    
                    logger.info(f"Buscando HPS para SOLICITANTE: {first_name} {last_name}")
                    
                    hps = db.query(HPSRequest).filter(
                        and_(
                            HPSRequest.first_name.ilike(f"%{first_name}%"),
                            HPSRequest.first_last_name.ilike(f"%{last_name}%"),
                            HPSRequest.status == "pending"  # Solo buscar en estado pending
                        )
                    ).first()
                    
                    if hps:
                        logger.info(f"HPS encontrada para SOLICITANTE: {hps.id}")
                        return hps
            
            # Buscar por número de documento del SOLICITANTE
            if email_info["document_number"]:
                logger.info(f"Buscando HPS por documento del SOLICITANTE: {email_info['document_number']}")
                
                hps = db.query(HPSRequest).filter(
                    and_(
                        HPSRequest.document_number == email_info["document_number"],
                        HPSRequest.status == "pending"
                    )
                ).first()
                
                if hps:
                    logger.info(f"HPS encontrada por documento del SOLICITANTE: {hps.id}")
                    return hps
            
            return None
            
        except Exception as e:
            logger.error(f"Error buscando HPS coincidente: {str(e)}")
            return None
    
    def _determine_new_status(self, email) -> Optional[str]:
        """
        Determina el nuevo estado basado en el contenido del correo
        
        Args:
            email: Objeto ReceivedEmail
            
        Returns:
            Nuevo estado o None si no se puede determinar
        """
        content = f"{email.subject} {email.body}".lower()
        
        # Verificar cada patrón de estado
        for status, patterns in self.status_patterns.items():
            for pattern in patterns:
                if re.search(pattern.lower(), content):
                    logger.info(f"Detectado cambio a estado: {status}")
                    return status
        
        return None
    
    def _send_status_notification(self, hps_request: HPSRequest, old_status: str, new_status: str, original_email, db: Session):
        """
        Envía notificación de cambio de estado incluyendo el correo original del gobierno
        
        Args:
            hps_request: Solicitud HPS actualizada
            old_status: Estado anterior
            new_status: Nuevo estado
            original_email: Correo original del gobierno que desencadenó el cambio
            db: Sesión de base de datos
        """
        try:
            # Obtener usuario
            user = db.query(User).filter(User.id == hps_request.user_id).first()
            
            if not user:
                logger.warning(f"Usuario no encontrado para HPS {hps_request.id}")
                return
            
            # Enviar correo de notificación con el correo original
            response = self.email_service.send_status_update_email(
                hps_request_id=hps_request.id,
                new_status=new_status,
                old_status=old_status,
                original_email=original_email,
                db=db
            )
            
            if response.success:
                logger.info(f"Notificación enviada a {user.email} para cambio de estado (incluye correo original)")
            else:
                logger.error(f"Error enviando notificación: {response.error}")
                
        except Exception as e:
            logger.error(f"Error enviando notificación de estado: {str(e)}")
    
    def get_monitoring_stats(self, db: Session, days: int = 7) -> Dict[str, Any]:
        """
        Obtiene estadísticas del sistema de monitorización
        
        Args:
            db: Sesión de base de datos
            days: Días hacia atrás para las estadísticas
            
        Returns:
            Dict con estadísticas
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Contar HPS por estado
            status_counts = {}
            for status in ["pending", "waiting_dps", "submitted", "approved", "rejected", "expired"]:
                count = db.query(HPSRequest).filter(
                    and_(
                        HPSRequest.status == status,
                        HPSRequest.updated_at >= since_date
                    )
                ).count()
                status_counts[status] = count
            
            return {
                "success": True,
                "period_days": days,
                "status_counts": status_counts,
                "total_processed": sum(status_counts.values())
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de monitorización: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
