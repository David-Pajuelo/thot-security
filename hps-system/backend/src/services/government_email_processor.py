#!/usr/bin/env python3
"""
Servicio de procesamiento automático de emails del gobierno con PDFs de HPS
"""

import os
import imaplib
import email
import tempfile
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

import PyPDF2
import pdfplumber
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.models.hps import HPSRequest
from src.models.user import User

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GovernmentEmailProcessor:
    """Procesador de emails del gobierno con PDFs de HPS"""
    
    def __init__(self, email_config: Dict[str, str]):
        """
        Inicializar procesador de emails
        
        Args:
            email_config: Configuración IMAP
            {
                'server': 'imap.gmail.com',
                'port': 993,
                'username': 'hps-system@empresa.com',
                'password': 'password_seguro',
                'folder': 'INBOX'
            }
        """
        self.email_config = email_config
        self.processed_files = set()
        
        # Patrones para identificar PDFs del gobierno
        self.government_pdf_patterns = [
            r'E-\d+-\d+-[A-Z]+-\d+_\d+\.pdf',  # E-25-027334-AICOX-0312_25.pdf
            r'E-\d+-\d+.*\.pdf',  # Variaciones del patrón
            r'.*HPS.*\.pdf',  # PDFs que contengan HPS
            r'.*LISTADO.*\.pdf',  # PDFs de listados
            r'.*CONCESI[OÓ]N.*\.pdf',  # PDFs de concesiones
            r'.*RECHAZO.*\.pdf'  # PDFs de rechazos
        ]
        
        # Remitentes autorizados del gobierno
        self.authorized_senders = [
            '@defensa.gob.es',
            '@mde.es', 
            '@inta.es',
            '@cni.es',
            # Añadir más dominios según sea necesario
        ]
    
    def connect_to_email(self) -> Optional[imaplib.IMAP4_SSL]:
        """Conectar al servidor IMAP"""
        try:
            mail = imaplib.IMAP4_SSL(self.email_config['server'], self.email_config['port'])
            mail.login(self.email_config['username'], self.email_config['password'])
            mail.select(self.email_config['folder'])
            logger.info(f"Conectado a {self.email_config['server']} como {self.email_config['username']}")
            return mail
        except Exception as e:
            logger.error(f"Error conectando al email: {e}")
            return None
    
    def is_government_sender(self, sender: str) -> bool:
        """Verificar si el remitente es del gobierno"""
        sender_lower = sender.lower()
        return any(domain in sender_lower for domain in self.authorized_senders)
    
    def is_government_pdf(self, filename: str) -> bool:
        """Verificar si el archivo PDF es del gobierno por su nombre"""
        filename_upper = filename.upper()
        
        # Verificar patrones específicos
        for pattern in self.government_pdf_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                logger.info(f"PDF del gobierno detectado por patrón: {filename}")
                return True
        
        return False
    
    def extract_pdf_content(self, pdf_path: str) -> Tuple[Optional[str], Optional[List]]:
        """Extraer contenido de un PDF"""
        try:
            text = ""
            tables = []
            
            # Usar pdfplumber para mejor extracción
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- PÁGINA {page_num + 1} ---\n"
                        text += page_text + "\n"
                    
                    # Extraer tablas
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table_num, table in enumerate(page_tables):
                            tables.append({
                                'page': page_num + 1,
                                'table': table_num + 1,
                                'data': table
                            })
            
            logger.info(f"PDF procesado: {len(text)} caracteres, {len(tables)} tablas")
            return text, tables
            
        except Exception as e:
            logger.error(f"Error extrayendo contenido del PDF {pdf_path}: {e}")
            return None, None
    
    def analyze_government_pdf(self, text: str, filename: str) -> Optional[Dict]:
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
        
        # Extraer información básica del documento
        empresa_match = re.search(r'Empresa:\s*([^N\n]+?)(?:NIF|$)', text, re.MULTILINE)
        nif_match = re.search(r'NIF:\s*([A-Z0-9]+)', text)
        fecha_match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
        expediente_match = re.search(r'(E-\d+-\d+)', text)
        
        doc_info = {
            'tipo_documento': doc_type,
            'empresa': empresa_match.group(1).strip() if empresa_match else 'DESCONOCIDA',
            'nif_empresa': nif_match.group(1) if nif_match else 'DESCONOCIDO',
            'fecha_documento': fecha_match.group(1) if fecha_match else None,
            'expediente_base': expediente_match.group(1) if expediente_match else 'DESCONOCIDO',
            'estado_general': status,
            'archivo_origen': filename
        }
        
        # Extraer personas del documento
        personas = self.extract_persons_from_text(text, status)
        
        result = {
            'documento': doc_info,
            'personas': personas,
            'total_personas': len(personas)
        }
        
        logger.info(f"Documento analizado: {doc_type}, {len(personas)} personas, empresa: {doc_info['empresa']}")
        return result
    
    def extract_persons_from_text(self, text: str, status: str) -> List[Dict]:
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
    
    def process_pdf_to_database(self, pdf_analysis: Dict, db: Session) -> List[str]:
        """Procesar análisis del PDF y actualizar base de datos"""
        processed_records = []
        
        try:
            for persona in pdf_analysis['personas']:
                dni = persona['dni']
                
                # Buscar usuario existente por DNI
                existing_hps = db.query(HPSRequest).filter(
                    HPSRequest.document_number == dni
                ).first()
                
                if existing_hps:
                    # Actualizar registro existente
                    existing_hps.status = 'approved' if persona['estado'] == 'APROBADO' else 'rejected'
                    existing_hps.expires_at = datetime.strptime(persona['fecha_fin'], '%d/%m/%Y').date()
                    existing_hps.approved_at = datetime.strptime(persona['fecha_inicio'], '%d/%m/%Y')
                    existing_hps.security_clearance_level = persona['grado_especialidad']
                    existing_hps.government_expediente = persona['expediente']
                    existing_hps.company_name = pdf_analysis['documento']['empresa']
                    existing_hps.company_nif = pdf_analysis['documento']['nif_empresa']
                    existing_hps.auto_processed = True
                    existing_hps.source_pdf_filename = pdf_analysis['documento']['archivo_origen']
                    existing_hps.auto_processed_at = datetime.now()
                    existing_hps.government_document_type = pdf_analysis['documento']['tipo_documento']
                    existing_hps.data_source = 'pdf_auto'
                    
                    logger.info(f"Actualizado registro existente para DNI: {dni}")
                    processed_records.append(f"ACTUALIZADO: {dni}")
                    
                else:
                    # Buscar usuario en la tabla users por DNI (si existe campo)
                    # Por ahora, crear registro básico
                    logger.warning(f"No se encontró registro HPS existente para DNI: {dni}")
                    processed_records.append(f"NO_ENCONTRADO: {dni}")
            
            db.commit()
            logger.info(f"Procesados {len(processed_records)} registros en BD")
            
        except Exception as e:
            logger.error(f"Error procesando PDF en BD: {e}")
            db.rollback()
            raise
        
        return processed_records
    
    def process_email_attachments(self, limit_emails: int = 10) -> Dict:
        """Procesar adjuntos PDF de emails recientes"""
        
        logger.info("Iniciando procesamiento de emails del gobierno...")
        
        mail = self.connect_to_email()
        if not mail:
            return {'error': 'No se pudo conectar al email'}
        
        try:
            # Buscar emails recientes (últimos 30 días)
            mail.search(None, 'SINCE "01-Dec-2024"')
            email_ids = mail.search(None, 'ALL')[1][0].split()
            
            # Limitar número de emails a procesar
            recent_emails = email_ids[-limit_emails:] if len(email_ids) > limit_emails else email_ids
            
            results = {
                'total_emails_checked': len(recent_emails),
                'government_emails_found': 0,
                'pdfs_processed': 0,
                'records_updated': 0,
                'errors': [],
                'processed_files': []
            }
            
            db = next(get_db())
            
            for email_id in recent_emails:
                try:
                    # Obtener email
                    _, msg_data = mail.fetch(email_id, '(RFC822)')
                    email_message = email.message_from_bytes(msg_data[0][1])
                    
                    # Verificar remitente
                    sender = email_message.get('From', '')
                    if not self.is_government_sender(sender):
                        continue
                    
                    results['government_emails_found'] += 1
                    logger.info(f"Email del gobierno encontrado de: {sender}")
                    
                    # Procesar adjuntos
                    for part in email_message.walk():
                        if part.get_content_disposition() == 'attachment':
                            filename = part.get_filename()
                            
                            if filename and filename.lower().endswith('.pdf'):
                                if self.is_government_pdf(filename):
                                    # Guardar PDF temporalmente
                                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                                        tmp_file.write(part.get_payload(decode=True))
                                        tmp_path = tmp_file.name
                                    
                                    try:
                                        # Procesar PDF
                                        text, tables = self.extract_pdf_content(tmp_path)
                                        if text:
                                            analysis = self.analyze_government_pdf(text, filename)
                                            if analysis:
                                                # Actualizar BD
                                                processed = self.process_pdf_to_database(analysis, db)
                                                
                                                results['pdfs_processed'] += 1
                                                results['records_updated'] += len(processed)
                                                results['processed_files'].append({
                                                    'filename': filename,
                                                    'sender': sender,
                                                    'type': analysis['documento']['tipo_documento'],
                                                    'total_personas': analysis['total_personas'],
                                                    'empresa': analysis['documento']['empresa'],
                                                    'records': processed
                                                })
                                                
                                                logger.info(f"PDF procesado exitosamente: {filename}")
                                    
                                    finally:
                                        # Limpiar archivo temporal
                                        os.unlink(tmp_path)
                
                except Exception as e:
                    error_msg = f"Error procesando email {email_id}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            return results
            
        except Exception as e:
            logger.error(f"Error general procesando emails: {e}")
            return {'error': str(e)}
        
        finally:
            mail.close()
            mail.logout()
    
    def run_scheduled_check(self) -> Dict:
        """Ejecutar verificación programada (para cron/scheduler)"""
        logger.info("=== VERIFICACIÓN PROGRAMADA DE EMAILS DEL GOBIERNO ===")
        
        start_time = datetime.now()
        results = self.process_email_attachments(limit_emails=50)
        end_time = datetime.now()
        
        # Log de resumen
        if 'error' not in results:
            logger.info(f"Verificación completada en {end_time - start_time}")
            logger.info(f"Emails verificados: {results['total_emails_checked']}")
            logger.info(f"Emails del gobierno: {results['government_emails_found']}")
            logger.info(f"PDFs procesados: {results['pdfs_processed']}")
            logger.info(f"Registros actualizados: {results['records_updated']}")
            
            if results['errors']:
                logger.warning(f"Errores encontrados: {len(results['errors'])}")
        else:
            logger.error(f"Error en verificación: {results['error']}")
        
        return results


# Configuración por defecto (usar la misma que otras automatizaciones)
DEFAULT_EMAIL_CONFIG = {
    'server': 'imap.gmail.com',
    'port': 993,
    'username': os.getenv('GOVERNMENT_EMAIL_USERNAME', 'hps-system@empresa.com'),
    'password': os.getenv('GOVERNMENT_EMAIL_PASSWORD', 'password_seguro'),
    'folder': 'INBOX'
}


def main():
    """Función principal para pruebas"""
    processor = GovernmentEmailProcessor(DEFAULT_EMAIL_CONFIG)
    results = processor.run_scheduled_check()
    
    print("RESULTADOS DEL PROCESAMIENTO:")
    print("=" * 50)
    
    if 'error' in results:
        print(f"ERROR: {results['error']}")
    else:
        print(f"Emails verificados: {results['total_emails_checked']}")
        print(f"Emails del gobierno: {results['government_emails_found']}")
        print(f"PDFs procesados: {results['pdfs_processed']}")
        print(f"Registros actualizados: {results['records_updated']}")
        
        if results['processed_files']:
            print(f"\nARCHIVOS PROCESADOS:")
            for file_info in results['processed_files']:
                print(f"- {file_info['filename']}")
                print(f"  Tipo: {file_info['type']}")
                print(f"  Empresa: {file_info['empresa']}")
                print(f"  Personas: {file_info['total_personas']}")
        
        if results['errors']:
            print(f"\nERRORES:")
            for error in results['errors']:
                print(f"- {error}")


if __name__ == "__main__":
    main()
