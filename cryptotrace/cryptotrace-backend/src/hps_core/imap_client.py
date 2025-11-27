"""
Cliente IMAP para recepción de correos electrónicos en Django
Adaptado desde hps-system/backend/src/email/imap_client.py
Maneja la conexión y lectura via Gmail IMAP
"""

import imaplib
import email
import ssl
from email.header import decode_header
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from django.conf import settings

logger = logging.getLogger(__name__)


class IMAPClient:
    """Cliente IMAP para recepción de correos"""
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        mailbox: Optional[str] = None
    ):
        """
        Inicializa el cliente IMAP con configuración de Django settings
        
        Args:
            host: Host IMAP (opcional, usa IMAP_HOST de settings si no se proporciona)
            port: Puerto IMAP (opcional, usa IMAP_PORT de settings si no se proporciona)
            username: Usuario IMAP (opcional, usa IMAP_USER de settings si no se proporciona)
            password: Contraseña IMAP (opcional, usa IMAP_PASSWORD de settings si no se proporciona)
            mailbox: Buzón IMAP (opcional, usa IMAP_MAILBOX de settings si no se proporciona)
        """
        self.host = host or getattr(settings, 'IMAP_HOST', 'imap.gmail.com')
        self.port = port or getattr(settings, 'IMAP_PORT', 993)
        self.username = username or getattr(settings, 'IMAP_USER', '')
        self.password = password or getattr(settings, 'IMAP_PASSWORD', '')
        self.mailbox = mailbox or getattr(settings, 'IMAP_MAILBOX', 'INBOX')
        self.connection: Optional[imaplib.IMAP4_SSL] = None
    
    def _create_connection(self) -> imaplib.IMAP4_SSL:
        """Crea una conexión IMAP segura"""
        try:
            # Crear contexto SSL
            context = ssl.create_default_context()
            
            # Conectar al servidor IMAP
            connection = imaplib.IMAP4_SSL(self.host, self.port, ssl_context=context)
            
            # Autenticar
            connection.login(self.username, self.password)
            
            # Seleccionar mailbox
            connection.select(self.mailbox)
            
            logger.info(f"Conectado exitosamente a IMAP {self.host}:{self.port}")
            return connection
            
        except Exception as e:
            logger.error(f"Error conectando a IMAP: {str(e)}")
            raise
    
    def _decode_header(self, header: str) -> str:
        """Decodifica headers de correo"""
        try:
            decoded_parts = decode_header(header)
            decoded_string = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding)
                    else:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += part
            
            return decoded_string
        except Exception as e:
            logger.error(f"Error decodificando header: {str(e)}")
            return header
    
    def _extract_email_body(self, msg: email.message.Message) -> str:
        """Extrae el cuerpo del correo"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Saltar adjuntos
                if "attachment" in content_disposition:
                    continue
                
                # Extraer texto
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8')
                        break
                    except:
                        continue
                elif content_type == "text/html" and not body:
                    try:
                        body = part.get_payload(decode=True).decode('utf-8')
                    except:
                        continue
        else:
            # Mensaje simple
            try:
                body = msg.get_payload(decode=True).decode('utf-8')
            except:
                body = str(msg.get_payload())
        
        return body
    
    def _extract_attachments(self, msg: email.message.Message) -> List[Dict[str, Any]]:
        """Extrae adjuntos del correo"""
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition"))
                
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        filename = self._decode_header(filename)
                        
                        try:
                            content = part.get_payload(decode=True)
                            attachments.append({
                                "filename": filename,
                                "content": content,
                                "content_type": part.get_content_type(),
                                "size": len(content) if content else 0
                            })
                        except Exception as e:
                            logger.error(f"Error extrayendo adjunto {filename}: {str(e)}")
        
        return attachments
    
    def _parse_email_date(self, date_str: str) -> datetime:
        """Parsea la fecha del correo"""
        try:
            # Intentar parsear con diferentes formatos
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except:
            try:
                # Formato común: "Mon, 1 Jan 2024 12:00:00 +0000"
                return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
            except:
                try:
                    # Sin timezone
                    return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S")
                except:
                    logger.warning(f"No se pudo parsear fecha: {date_str}, usando fecha actual")
                    return datetime.utcnow()
    
    def get_unread_emails(self, since_days: int = 1) -> List[Dict[str, Any]]:
        """
        Obtiene correos no leídos desde hace X días
        
        Args:
            since_days: Días hacia atrás para buscar correos
            
        Returns:
            Lista de diccionarios con información de correos recibidos
        """
        try:
            connection = self._create_connection()
            
            # Calcular fecha desde
            since_date = (datetime.now() - timedelta(days=since_days)).strftime("%d-%b-%Y")
            
            # Buscar correos no leídos
            search_criteria = f'(UNSEEN SINCE "{since_date}")'
            status, messages = connection.search(None, search_criteria)
            
            if status != 'OK':
                logger.error("Error buscando correos")
                connection.close()
                connection.logout()
                return []
            
            email_ids = messages[0].split()
            emails = []
            
            for email_id in email_ids:
                try:
                    # Obtener el correo
                    status, msg_data = connection.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    # Parsear el correo
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # Extraer información
                    from_email = self._decode_header(msg.get('From', ''))
                    subject = self._decode_header(msg.get('Subject', ''))
                    date_str = msg.get('Date', '')
                    message_id = msg.get('Message-ID', '')
                    to_email = self._decode_header(msg.get('To', ''))
                    
                    # Parsear fecha
                    received_at = self._parse_email_date(date_str)
                    
                    # Extraer cuerpo y adjuntos
                    body = self._extract_email_body(msg)
                    attachments = self._extract_attachments(msg)
                    
                    # Crear diccionario con información del correo
                    email_data = {
                        "message_id": message_id,
                        "from_email": from_email,
                        "to_email": to_email,
                        "subject": subject,
                        "body": body,
                        "received_at": received_at,
                        "is_read": False,
                        "attachments": attachments if attachments else [],
                        "raw_message": raw_email  # Para procesamiento adicional si es necesario
                    }
                    
                    emails.append(email_data)
                    
                except Exception as e:
                    logger.error(f"Error procesando correo {email_id}: {str(e)}")
                    continue
            
            connection.close()
            connection.logout()
            
            logger.info(f"Obtenidos {len(emails)} correos no leídos")
            return emails
            
        except Exception as e:
            logger.error(f"Error obteniendo correos: {str(e)}")
            return []
    
    def mark_as_read(self, message_id: str) -> bool:
        """
        Marca un correo como leído
        
        Args:
            message_id: ID del mensaje a marcar (Message-ID del correo)
            
        Returns:
            True si se marcó exitosamente
        """
        try:
            connection = self._create_connection()
            
            # Buscar el correo por Message-ID
            search_criteria = f'(HEADER Message-ID "{message_id}")'
            status, messages = connection.search(None, search_criteria)
            
            if status != 'OK' or not messages[0]:
                logger.error(f"Correo no encontrado: {message_id}")
                connection.close()
                connection.logout()
                return False
            
            email_ids = messages[0].split()
            
            # Marcar como leído
            for email_id in email_ids:
                connection.store(email_id, '+FLAGS', '\\Seen')
            
            connection.close()
            connection.logout()
            
            logger.info(f"Correo marcado como leído: {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error marcando correo como leído: {str(e)}")
            return False
    
    def mark_as_read_by_uid(self, uid: str) -> bool:
        """
        Marca un correo como leído por su UID
        
        Args:
            uid: UID del correo en el servidor IMAP
            
        Returns:
            True si se marcó exitosamente
        """
        try:
            connection = self._create_connection()
            
            # Marcar como leído
            connection.store(uid, '+FLAGS', '\\Seen')
            
            connection.close()
            connection.logout()
            
            logger.info(f"Correo marcado como leído (UID: {uid})")
            return True
            
        except Exception as e:
            logger.error(f"Error marcando correo como leído (UID: {uid}): {str(e)}")
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Prueba la conexión IMAP
        
        Returns:
            Dict con el resultado de la prueba
        """
        try:
            connection = self._create_connection()
            connection.close()
            connection.logout()
            
            return {
                "success": True,
                "message": "Conexión IMAP exitosa",
                "host": self.host,
                "port": self.port,
                "username": self.username,
                "mailbox": self.mailbox
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error de conexión: {str(e)}",
                "host": self.host,
                "port": self.port,
                "username": self.username,
                "mailbox": self.mailbox
            }
    
    def get_all_emails(self, since_days: int = 1, read: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Obtiene todos los correos (leídos y no leídos) desde hace X días
        
        Args:
            since_days: Días hacia atrás para buscar correos
            read: Si es True, solo leídos; si es False, solo no leídos; si es None, todos
            
        Returns:
            Lista de diccionarios con información de correos
        """
        try:
            connection = self._create_connection()
            
            # Calcular fecha desde
            since_date = (datetime.now() - timedelta(days=since_days)).strftime("%d-%b-%Y")
            
            # Construir criterio de búsqueda
            if read is True:
                search_criteria = f'(SEEN SINCE "{since_date}")'
            elif read is False:
                search_criteria = f'(UNSEEN SINCE "{since_date}")'
            else:
                search_criteria = f'(SINCE "{since_date}")'
            
            status, messages = connection.search(None, search_criteria)
            
            if status != 'OK':
                logger.error("Error buscando correos")
                connection.close()
                connection.logout()
                return []
            
            email_ids = messages[0].split()
            emails = []
            
            for email_id in email_ids:
                try:
                    # Obtener el correo
                    status, msg_data = connection.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    # Parsear el correo
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # Extraer información
                    from_email = self._decode_header(msg.get('From', ''))
                    subject = self._decode_header(msg.get('Subject', ''))
                    date_str = msg.get('Date', '')
                    message_id = msg.get('Message-ID', '')
                    to_email = self._decode_header(msg.get('To', ''))
                    
                    # Parsear fecha
                    received_at = self._parse_email_date(date_str)
                    
                    # Extraer cuerpo y adjuntos
                    body = self._extract_email_body(msg)
                    attachments = self._extract_attachments(msg)
                    
                    # Verificar si está leído
                    flags = connection.fetch(email_id, '(FLAGS)')[1][0].decode()
                    is_read = '\\Seen' in flags
                    
                    # Crear diccionario con información del correo
                    email_data = {
                        "message_id": message_id,
                        "from_email": from_email,
                        "to_email": to_email,
                        "subject": subject,
                        "body": body,
                        "received_at": received_at,
                        "is_read": is_read,
                        "attachments": attachments if attachments else [],
                        "uid": email_id.decode() if isinstance(email_id, bytes) else str(email_id)
                    }
                    
                    emails.append(email_data)
                    
                except Exception as e:
                    logger.error(f"Error procesando correo {email_id}: {str(e)}")
                    continue
            
            connection.close()
            connection.logout()
            
            logger.info(f"Obtenidos {len(emails)} correos")
            return emails
            
        except Exception as e:
            logger.error(f"Error obteniendo correos: {str(e)}")
            return []

