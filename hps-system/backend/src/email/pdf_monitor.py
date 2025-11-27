"""
Monitor extendido para procesar PDFs adjuntos del gobierno
"""

import tempfile
import os
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .hps_monitor import HPSEmailMonitor
from .schemas import ReceivedEmail

logger = logging.getLogger(__name__)

class PDFEmailMonitor(HPSEmailMonitor):
    """Monitor extendido para procesar PDFs adjuntos"""
    
    def __init__(self, email_service):
        super().__init__(email_service)
        
        # Patrones para identificar PDFs del gobierno
        self.government_pdf_patterns = [
            r'E-\d+-\d+-[A-Z]+-\d+_\d+\.pdf',  # E-25-027334-AICOX-0312_25.pdf
            r'E-\d+-\d+.*\.pdf',                # Variaciones del patrón
            r'.*HPS.*\.pdf',                    # PDFs que contengan HPS
            r'.*LISTADO.*\.pdf',                # PDFs de listados
            r'.*CONCESI[OÓ]N.*\.pdf',          # PDFs de concesiones
            r'.*RECHAZO.*\.pdf'                 # PDFs de rechazos
        ]
    
    def _is_government_pdf(self, filename: str) -> bool:
        """Verificar si el archivo PDF es del gobierno por su nombre"""
        filename_upper = filename.upper()
        
        for pattern in self.government_pdf_patterns:
            if re.search(pattern, filename_upper, re.IGNORECASE):
                logger.info(f"PDF del gobierno detectado por patrón: {filename}")
                return True
        
        return False
    
    def _process_pdf_attachment(self, attachment: Dict[str, Any], db) -> Dict[str, Any]:
        """Procesar un adjunto PDF del gobierno"""
        try:
            filename = attachment.get('filename', '')
            content = attachment.get('content', b'')
            content_type = attachment.get('content_type', '')
            
            # Verificar que es un PDF
            if not content_type.startswith('application/pdf'):
                return {"processed": False, "reason": "No es un PDF"}
            
            # Verificar si es un PDF del gobierno
            if not self._is_government_pdf(filename):
                return {"processed": False, "reason": "No es un PDF del gobierno"}
            
            logger.info(f"Procesando PDF del gobierno: {filename}")
            
            # Guardar temporalmente para procesamiento
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            try:
                # Extraer texto del PDF
                text = self._extract_pdf_text(tmp_path)
                if not text:
                    return {"processed": False, "reason": "No se pudo extraer texto del PDF"}
                
                # Analizar el PDF
                analysis = self._analyze_government_pdf(text, filename)
                if not analysis:
                    return {"processed": False, "reason": "No se pudo analizar el PDF"}
                
                # Procesar personas encontradas
                processed_count = self._process_persons_from_pdf(analysis, db)
                
                return {
                    "processed": True,
                    "filename": filename,
                    "persons_found": len(analysis.get('personas', [])),
                    "processed_count": processed_count
                }
                
            finally:
                # Limpiar archivo temporal
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            logger.error(f"Error procesando PDF {filename}: {str(e)}")
            return {"processed": False, "reason": f"Error: {str(e)}"}
    
    def _extract_pdf_text(self, pdf_path: str) -> Optional[str]:
        """Extraer texto de un PDF"""
        try:
            import pdfplumber
            
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            return text.strip() if text else None
            
        except ImportError:
            logger.error("pdfplumber no está instalado")
            return None
        except Exception as e:
            logger.error(f"Error extrayendo texto del PDF: {str(e)}")
            return None
    
    def _analyze_government_pdf(self, text: str, filename: str) -> Optional[Dict]:
        """Analizar contenido del PDF del gobierno"""
        if not text:
            return None
        
        # Determinar tipo de documento
        text_upper = text.upper()
        
        if 'LISTADO DE CONCESIONES' in text_upper or 'CONCEDID' in text_upper:
            doc_type = 'LISTADO_CONCESIONES'
            status = 'APROBADO'
        elif 'LISTADO DE RECHAZOS' in text_upper or 'RECHAZAD' in text_upper or 'DENEGAD' in text_upper:
            doc_type = 'LISTADO_RECHAZOS'
            status = 'RECHAZADO'
        else:
            logger.warning(f"Tipo de documento no reconocido en {filename}")
            return None
        
        # Extraer personas del documento
        personas = self._extract_persons_from_text(text, status)
        
        result = {
            'documento': {
                'tipo_documento': doc_type,
                'estado_general': status,
                'archivo_origen': filename
            },
            'personas': personas,
            'total_personas': len(personas)
        }
        
        logger.info(f"Documento analizado: {doc_type}, {len(personas)} personas")
        return result
    
    def _extract_persons_from_text(self, text: str, status: str) -> List[Dict]:
        """Extraer personas del texto del PDF"""
        personas = []
        
        # Patrón para extraer líneas con DNI y datos
        pattern = r'(\d+)\s+([0-9]{8}[A-Z])\s+(.*?)\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+(E-\d+-\d+)'
        matches = re.findall(pattern, text)
        
        for match in matches:
            numero, dni, grado_especialidad, fecha_inicio, fecha_fin, expediente = match
            
            personas.append({
                'numero': int(numero),
                'dni': dni,
                'grado_especialidad': grado_especialidad.strip(),
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'expediente': expediente,
                'estado': status
            })
        
        return personas
    
    def _process_persons_from_pdf(self, analysis: Dict, db) -> int:
        """Procesar personas encontradas en el PDF y actualizar base de datos"""
        processed_count = 0
        
        try:
            for persona in analysis['personas']:
                dni = persona['dni']
                
                # Buscar HPS existente por DNI
                from src.models.hps import HPSRequest
                
                existing_hps = db.query(HPSRequest).filter(
                    HPSRequest.document_number == dni
                ).first()
                
                if existing_hps:
                    # Actualizar registro existente
                    new_status = 'approved' if persona['estado'] == 'APROBADO' else 'rejected'
                    
                    if existing_hps.status != new_status:
                        old_status = existing_hps.status
                        existing_hps.status = new_status
                        existing_hps.expires_at = datetime.strptime(persona['fecha_fin'], '%d/%m/%Y').date()
                        existing_hps.approved_at = datetime.strptime(persona['fecha_inicio'], '%d/%m/%Y')
                        existing_hps.security_clearance_level = persona['grado_especialidad']
                        existing_hps.government_expediente = persona['expediente']
                        existing_hps.auto_processed = True
                        existing_hps.source_pdf_filename = analysis['documento']['archivo_origen']
                        existing_hps.auto_processed_at = datetime.now()
                        existing_hps.government_document_type = analysis['documento']['tipo_documento']
                        existing_hps.data_source = 'pdf_auto'
                        
                        db.commit()
                        
                        logger.info(f"Actualizado registro para DNI: {dni} ({old_status} -> {new_status})")
                        processed_count += 1
                    else:
                        logger.info(f"Registro para DNI {dni} ya está en estado {new_status}")
                else:
                    logger.warning(f"No se encontró registro HPS para DNI: {dni}")
            
        except Exception as e:
            logger.error(f"Error procesando personas del PDF: {str(e)}")
            db.rollback()
            raise
        
        return processed_count
    
    def monitor_emails_with_pdfs(self, db, since_days: int = 1) -> Dict[str, Any]:
        """Monitorizar correos incluyendo procesamiento de PDFs"""
        try:
            # Obtener correos nuevos usando IMAPClient
            new_emails = self.email_service.imap_client.get_unread_emails(since_days)
            
            if not new_emails:
                logger.info("No hay correos nuevos para procesar")
                return {
                    "success": True,
                    "emails_processed": 0,
                    "pdfs_processed": 0,
                    "status_updates": 0,
                    "errors": []
                }
            
            logger.info(f"Procesando {len(new_emails)} correos nuevos")
            
            processed_count = 0
            pdfs_processed = 0
            status_updates = 0
            errors = []
            
            for email in new_emails:
                try:
                    # Verificar si es un correo del gobierno
                    if self._is_government_email(email):
                        logger.info(f"Procesando correo del gobierno: {email.subject}")
                        
                        # Procesar adjuntos PDF
                        if email.attachments:
                            for attachment in email.attachments:
                                pdf_result = self._process_pdf_attachment(attachment, db)
                                if pdf_result.get('processed'):
                                    pdfs_processed += 1
                                    status_updates += pdf_result.get('processed_count', 0)
                                    logger.info(f"PDF procesado: {pdf_result['filename']}")
                        
                        # Procesar correo normal (sin adjuntos)
                        result = self._process_government_email(email, db)
                        if result["status_updated"]:
                            status_updates += 1
                        
                        processed_count += 1
                        
                        # Marcar como leído
                        self.email_service.imap_client.mark_as_read(email.message_id)
                        
                except Exception as e:
                    error_msg = f"Error procesando correo {email.message_id}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            logger.info(f"Monitorización completada: {processed_count} correos, {pdfs_processed} PDFs, {status_updates} actualizaciones")
            
            return {
                "success": True,
                "emails_processed": processed_count,
                "pdfs_processed": pdfs_processed,
                "status_updates": status_updates,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error en monitorización de correos: {str(e)}")
            return {
                "success": False,
                "emails_processed": 0,
                "pdfs_processed": 0,
                "status_updates": 0,
                "errors": [str(e)]
            }
