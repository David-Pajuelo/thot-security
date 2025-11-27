"""
Servicio para manipulación de PDFs
"""
import io
from typing import Dict, Any, Optional
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import logging

logger = logging.getLogger(__name__)

class PDFService:
    """Servicio para manipular PDFs"""
    
    @staticmethod
    def _format_date_spanish(date_value):
        """
        Convierte una fecha ISO (YYYY-MM-DD) al formato español (DD/MM/YYYY)
        
        Args:
            date_value: Fecha en formato ISO o objeto date
            
        Returns:
            Fecha formateada en español o string vacío si no es válida
        """
        try:
            if not date_value:
                return ""
            
            # Si es string, convertir a date
            if isinstance(date_value, str):
                from datetime import datetime
                date_obj = datetime.strptime(date_value, "%Y-%m-%d").date()
            else:
                date_obj = date_value
            
            # Formatear a DD/MM/YYYY
            return date_obj.strftime("%d/%m/%Y")
            
        except (ValueError, AttributeError, TypeError):
            return str(date_value) if date_value else ""
    
    @staticmethod
    def fill_pdf_template(template_pdf_bytes: bytes, user_data: Dict[str, Any]) -> bytes:
        """
        Rellena un PDF template con los datos del usuario usando PyMuPDF
        
        Args:
            template_pdf_bytes: Bytes del PDF template
            user_data: Diccionario con los datos del usuario
            
        Returns:
            Bytes del PDF rellenado
        """
        try:
            import fitz  # PyMuPDF
            
            # Mapear datos del usuario a campos del formulario (solo los campos básicos)
            # Aplicar conversión a mayúsculas excepto para el email
            field_mapping = {
                "Nombre": user_data.get("first_name", "").upper(),
                "Apellidos": f"{user_data.get('first_last_name', '')} {user_data.get('second_last_name', '')}".strip().upper(),
                "DNI": user_data.get("document_number", "").upper(),
                "Fecha de nacimiento": PDFService._format_date_spanish(user_data.get("birth_date", "")),
                "Nacionalidad": user_data.get("nationality", "").upper(),
                "LugarNacimiento": user_data.get("birth_place", "").upper(),
                "Teléfono": user_data.get("phone", "").upper(),
                "Email": user_data.get("email", ""),  # Email se mantiene en minúsculas
                # Campo automático para motivo de la solicitud
                "Motivo de la solicitudRow1": f"{user_data.get('first_name', '')} {user_data.get('first_last_name', '')} va a participar en proyectos para los que necesita acceso a documentación clasificada."
            }
            
            # Crear documento desde bytes
            doc = fitz.open(stream=template_pdf_bytes, filetype="pdf")
            
            # Obtener la primera página
            page = doc[0]
            
            # Buscar widgets (campos de formulario)
            widgets = list(page.widgets())
            logger.info(f"Encontrados {len(widgets)} widgets en el PDF")
            
            # Rellenar los campos
            fields_filled = 0
            for widget in widgets:
                try:
                    field_name = widget.field_name
                    if field_name in field_mapping and field_mapping[field_name]:
                        widget.field_value = field_mapping[field_name]
                        widget.update()
                        fields_filled += 1
                        logger.info(f"Campo '{field_name}' rellenado con: {field_mapping[field_name]}")
                except Exception as e:
                    logger.warning(f"Error rellenando campo '{field_name}': {str(e)}")
                    continue
            
            logger.info(f"Total campos rellenados: {fields_filled}")
            
            # Crear buffer de salida
            output_buffer = io.BytesIO()
            doc.save(output_buffer)
            doc.close()
            output_buffer.seek(0)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error rellenando PDF con PyMuPDF: {str(e)}")
            # Fallback: usar superposición de texto
            logger.info("Fallback: usando superposición de texto")
            return PDFService.overlay_text_on_template(template_pdf_bytes, user_data)
    
    @staticmethod
    def overlay_text_on_template(template_pdf_bytes: bytes, user_data: Dict[str, Any]) -> bytes:
        """
        Superpone texto sobre una plantilla PDF sin campos de formulario
        
        Args:
            template_pdf_bytes: Bytes del PDF template
            user_data: Diccionario con los datos del usuario
            
        Returns:
            Bytes del PDF con texto superpuesto
        """
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.colors import black
            
            # Usar la plantilla como base y superponer texto
            logger.info("Usando plantilla como base y superponiendo texto")
            
            # Leer la plantilla
            template_reader = PdfReader(io.BytesIO(template_pdf_bytes))
            writer = PdfWriter()
            
            # Copiar todas las páginas de la plantilla
            for page in template_reader.pages:
                writer.add_page(page)
            
            # Crear una capa de texto superpuesta
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            can.setFont("Helvetica", 10)
            can.setFillColor(black)
            
            # Posiciones para superponer datos
            y_position = 700
            x_position = 100
            
            # Superponer datos del usuario
            for field, value in user_data.items():
                if value:
                    can.drawString(x_position, y_position, f"{field.replace('_', ' ').title()}: {str(value)}")
                    y_position -= 20
            
            can.save()
            packet.seek(0)
            
            # Crear PDF de superposición
            overlay_reader = PdfReader(packet)
            overlay_page = overlay_reader.pages[0]
            
            # Superponer sobre la primera página de la plantilla
            if len(template_reader.pages) > 0:
                template_reader.pages[0].merge_page(overlay_page)
            
            # Crear buffer de salida
            output_buffer = io.BytesIO()
            writer.write(output_buffer)
            output_buffer.seek(0)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error superponiendo texto en template: {str(e)}")
            # Fallback: crear PDF simple
            logger.info("Fallback: creando PDF simple")
            return PDFService.create_simple_filled_pdf(user_data)
    
    @staticmethod
    def create_simple_filled_pdf(user_data: Dict[str, Any]) -> bytes:
        """
        Crea un PDF simple con los datos del usuario
        (Fallback si no se puede rellenar el template)
        """
        try:
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            # Título
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, height - 100, "Solicitud de Traslado HPS")
            
            # Datos del usuario
            y_position = height - 150
            c.setFont("Helvetica", 12)
            
            data_fields = [
                ("Nombre:", user_data.get('first_name', '')),
                ("Apellidos:", f"{user_data.get('first_last_name', '')} {user_data.get('second_last_name', '')}".strip()),
                ("Email:", user_data.get('email', '')),
                ("Teléfono:", user_data.get('phone', '')),
                ("DNI/NIE:", user_data.get('document_number', '')),
                ("Fecha de nacimiento:", PDFService._format_date_spanish(user_data.get('birth_date', ''))),
                ("Lugar de nacimiento:", user_data.get('birth_place', '')),
                ("Nacionalidad:", user_data.get('nationality', '')),
            ]
            
            for field, value in data_fields:
                c.drawString(100, y_position, f"{field} {value}")
                y_position -= 25
            
            c.save()
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error creando PDF simple: {str(e)}")
            raise ValueError(f"Error creando PDF simple: {str(e)}")
    
    @staticmethod
    def edit_existing_pdf(pdf_bytes: bytes, field_updates: Dict[str, Any]) -> bytes:
        """
        Editar un PDF existente actualizando campos específicos
        
        Args:
            pdf_bytes: Bytes del PDF existente
            field_updates: Diccionario con los campos a actualizar
            
        Returns:
            Bytes del PDF editado
        """
        try:
            import fitz  # PyMuPDF
            
            # Crear documento desde bytes
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # Obtener la primera página
            page = doc[0]
            
            # Buscar widgets (campos de formulario)
            widgets = list(page.widgets())
            logger.info(f"Encontrados {len(widgets)} widgets en el PDF")
            
            # Actualizar solo los campos especificados
            fields_updated = 0
            for widget in widgets:
                try:
                    field_name = widget.field_name
                    if field_name in field_updates and field_updates[field_name]:
                        # Formatear fecha si es necesario
                        if 'fecha' in field_name.lower() and field_updates[field_name]:
                            widget.field_value = PDFService._format_date_spanish(field_updates[field_name])
                        else:
                            widget.field_value = field_updates[field_name]
                        widget.update()
                        fields_updated += 1
                        logger.info(f"Campo '{field_name}' actualizado con: {field_updates[field_name]}")
                except Exception as e:
                    logger.warning(f"Error actualizando campo '{field_name}': {str(e)}")
                    continue
            
            logger.info(f"Total campos actualizados: {fields_updated}")
            
            # Crear buffer de salida
            output_buffer = io.BytesIO()
            doc.save(output_buffer)
            doc.close()
            output_buffer.seek(0)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error editando PDF con PyMuPDF: {str(e)}")
            raise ValueError(f"Error editando PDF: {str(e)}")

    @staticmethod
    def extract_pdf_fields(pdf_bytes: bytes) -> Dict[str, str]:
        """
        Extraer campos del PDF usando PyMuPDF
        
        Args:
            pdf_bytes: Bytes del PDF
            
        Returns:
            Diccionario con los campos extraídos
        """
        try:
            import fitz  # PyMuPDF
            
            # Crear documento desde bytes
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # Obtener la primera página
            page = doc[0]
            
            # Buscar widgets (campos de formulario)
            widgets = list(page.widgets())
            logger.info(f"Encontrados {len(widgets)} widgets en el PDF")
            
            # Extraer valores de los campos
            extracted_fields = {}
            for widget in widgets:
                try:
                    field_name = widget.field_name
                    field_value = widget.field_value
                    
                    # Extraer todos los campos (incluyendo vacíos)
                    if field_name:
                        # Convertir a string, manejar None y valores vacíos
                        if field_value is None:
                            extracted_fields[field_name] = ""
                        else:
                            extracted_fields[field_name] = str(field_value).strip()
                        logger.info(f"Campo extraído: '{field_name}' = '{extracted_fields[field_name]}'")
                except Exception as e:
                    logger.warning(f"Error extrayendo campo '{field_name}': {str(e)}")
                    continue
            
            doc.close()
            logger.info(f"Total campos extraídos: {len(extracted_fields)}")
            
            return extracted_fields
            
        except Exception as e:
            logger.error(f"Error extrayendo campos del PDF con PyMuPDF: {str(e)}")
            raise ValueError(f"Error extrayendo campos del PDF: {str(e)}")
