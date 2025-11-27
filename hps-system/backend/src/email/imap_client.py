"""
Cliente IMAP para recepción de correos electrónicos
Maneja la conexión y lectura via Gmail IMAP
"""

import imaplib
import email
import ssl
from email.header import decode_header
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import re

from .schemas import ReceivedEmail

logger = logging.getLogger(__name__)


class IMAPClient:
    """Cliente IMAP para recepción de correos"""
    
    def __init__(
        self,
        host: str = "imap.gmail.com",
        port: int = 993,
        username: str = "",
        password: str = "",
        mailbox: str = "INBOX"
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.mailbox = mailbox
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
    
    def get_unread_emails(self, since_days: int = 1) -> List[ReceivedEmail]:
        """
        Obtiene correos no leídos desde hace X días
        
        Args:
            since_days: Días hacia atrás para buscar correos
            
        Returns:
            Lista de correos recibidos
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
                    
                    # Parsear fecha
                    try:
                        received_at = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
                    except:
                        received_at = datetime.utcnow()
                    
                    # Extraer cuerpo y adjuntos
                    body = self._extract_email_body(msg)
                    attachments = self._extract_attachments(msg)
                    
                    # Crear objeto ReceivedEmail
                    received_email = ReceivedEmail(
                        message_id=message_id,
                        from_email=from_email,
                        subject=subject,
                        body=body,
                        received_at=received_at,
                        is_read=False,
                        attachments=attachments if attachments else None
                    )
                    
                    emails.append(received_email)
                    
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
            message_id: ID del mensaje a marcar
            
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
