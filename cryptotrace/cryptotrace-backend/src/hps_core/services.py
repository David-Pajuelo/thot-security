from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import transaction
from django.db.models import Case, When, IntegerField
from django.utils import timezone

from .models import HpsRequest, HpsToken, HpsTemplate
from .tasks import send_hps_credentials_email
from .email_service import HpsEmailService

logger = logging.getLogger(__name__)
email_service = HpsEmailService()
User = get_user_model()


@dataclass
class TokenMetadata:
    email: str
    requested_by_id: int
    purpose: Optional[str] = None
    hours_valid: int = 72


class HpsTokenService:
    @staticmethod
    def create_token(meta: TokenMetadata) -> HpsToken:
        expires = timezone.now() + timedelta(hours=meta.hours_valid)
        token = HpsToken.objects.create(
            email=meta.email,
            requested_by_id=meta.requested_by_id,
            purpose=meta.purpose or "",
            expires_at=expires,
        )
        logger.info("Token HPS creado para %s expira %s", meta.email, expires)
        return token

    @staticmethod
    def mark_used(token: HpsToken):
        token.is_used = True
        token.used_at = timezone.now()
        token.save(update_fields=["is_used", "used_at"])


class HpsRequestService:
    @staticmethod
    @transaction.atomic
    def create_from_token(*, serializer, token: HpsToken, form_type: str):
        """
        Crear solicitud HPS desde un token público.
        
        El usuario se crea o busca basado en el email del token, no en token.requested_by.
        Si el usuario no existe, se crea automáticamente con un perfil HPS básico.
        """
        # Normalizar y validar form_type
        form_type_lower = form_type.lower().strip() if form_type else "solicitud"
        if form_type_lower in ["traslado", "traspaso", "transfer", "trasladar", "traspasar"]:
            form_type = "traslado"
        else:
            # Por defecto, cualquier otro valor se convierte a "solicitud"
            form_type = "solicitud"
        
        # Obtener el email del formulario o del token
        form_email = serializer.validated_data.get("email") or token.email
        
        # Buscar o crear el usuario basado en el email del token
        user_created = False
        temp_password = None
        try:
            user = User.objects.get(email=form_email)
        except User.DoesNotExist:
            # Crear nuevo usuario si no existe
            # Generar contraseña temporal antes de crear el usuario
            from django.contrib.auth.hashers import make_password
            import secrets
            import string
            
            # Generar contraseña temporal segura (12 caracteres)
            # Usar solo caracteres alfanuméricos para evitar problemas al copiar del email
            # Excluir caracteres que pueden confundirse: 0, O, 1, l, I
            alphabet = string.ascii_letters.replace('O', '').replace('o', '').replace('I', '').replace('l', '') + \
                      string.digits.replace('0', '').replace('1', '')
            temp_password = ''.join(secrets.choice(alphabet) for i in range(12))
            
            # Log de la contraseña generada (solo en desarrollo, no en producción)
            logger.info(f"Contraseña temporal generada para {form_email}: {temp_password}")
            
            # Usar el email completo como username para que coincida con lo que envía el frontend
            # El frontend envía el email como 'username' en el login
            username = form_email  # Usar email completo como username
            # Asegurar que el username sea único (aunque el email ya debería serlo)
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Obtener nombre del formulario si está disponible
            first_name = serializer.validated_data.get("first_name", "")
            last_name = serializer.validated_data.get("first_last_name", "")
            
            # Crear usuario con contraseña temporal
            # Usar create_user con password para asegurar que se guarde correctamente
            user = User.objects.create_user(
                username=username,
                email=form_email,
                password=temp_password,  # Pasar la contraseña directamente
                first_name=first_name,
                last_name=last_name,
                is_active=True,
            )
            
            # El signal debería crear el perfil automáticamente después de save()
            # Refrescar el usuario desde la BD para asegurar que el signal se ejecutó
            user.refresh_from_db()
            
            # Obtener el perfil (debería existir gracias al signal)
            from .models import HpsUserProfile, HpsTeam
            import uuid
            
            # Obtener o crear el equipo AICOX
            AICOX_TEAM_UUID = uuid.UUID('d8574c01-851f-4716-9ac9-bbda45469bdf')
            try:
                aicox_team = HpsTeam.objects.get(id=AICOX_TEAM_UUID)
            except HpsTeam.DoesNotExist:
                aicox_team = HpsTeam.objects.filter(name__iexact='AICOX').first()
                if not aicox_team:
                    aicox_team = HpsTeam.objects.create(
                        id=AICOX_TEAM_UUID,
                        name='AICOX',
                        description='Equipo genérico AICOX',
                        is_active=True
                    )
            
            try:
                profile = user.hps_profile
                # Asegurar que el perfil tenga el equipo AICOX asignado
                if not profile.team:
                    profile.team = aicox_team
                profile.is_temp_password = True
                profile.must_change_password = True
                profile.save(update_fields=['team', 'is_temp_password', 'must_change_password'])
            except HpsUserProfile.DoesNotExist:
                # Si por alguna razón no existe, crearlo con el equipo AICOX
                profile = HpsUserProfile.objects.create(
                    user=user,
                    team=aicox_team,
                    is_temp_password=True,
                    must_change_password=True,
                )
            
            user_created = True
            logger.info(f"Usuario creado automáticamente para email: {form_email} con contraseña temporal")
        
        # Determinar request_type basado en form_type
        # Si form_type es "traslado", entonces request_type debe ser "transfer"
        if form_type == "traslado":
            request_type = HpsRequest.RequestType.TRANSFER
        else:
            # Para "solicitud", determinar si es nueva o renovación
            # Por defecto, asumimos que es nueva (NEW)
            request_type = HpsRequest.RequestType.NEW
            
            # Si el usuario ya tiene una HPS aprobada, podría ser una renovación
            # Pero por ahora, lo dejamos como NEW para nuevas solicitudes desde token
            # La lógica de renovación se puede añadir más adelante
        
        # Buscar una plantilla activa para asociar
        # Si es un traslado, seleccionar plantilla según el rol del solicitante (token.requested_by)
        template = None
        if form_type == "traslado":
            # Obtener el rol del usuario que solicitó el traspaso
            requested_by_user = token.requested_by
            requested_by_role = None
            try:
                requested_by_profile = requested_by_user.hps_profile
                requested_by_role = requested_by_profile.role.name if requested_by_profile.role else None
            except Exception:
                # Si no tiene perfil, verificar si es superuser (admin)
                if requested_by_user.is_superuser:
                    requested_by_role = "admin"
            
            # Determinar qué tipo de plantilla usar según el rol del solicitante
            # Si es admin o jefe_seguridad → usar plantilla de jefe_seguridad
            # Si es jefe_seguridad_suplente → usar plantilla de jefe_seguridad_suplente
            if requested_by_role in ["admin", "jefe_seguridad", "security_chief"]:
                # Buscar plantilla de jefe de seguridad
                template = HpsTemplate.objects.filter(
                    active=True,
                    template_type=HpsTemplate.TemplateType.JEFE
                ).first()
                logger.info(
                    f"Solicitante es {requested_by_role}, usando plantilla de jefe de seguridad. "
                    f"Email del token: {token.email}"
                )
            elif requested_by_role == "jefe_seguridad_suplente":
                # Buscar plantilla de jefe de seguridad suplente
                template = HpsTemplate.objects.filter(
                    active=True,
                    template_type=HpsTemplate.TemplateType.SUPLENTE
                ).first()
                logger.info(
                    f"Solicitante es {requested_by_role}, usando plantilla de jefe de seguridad suplente. "
                    f"Email del token: {token.email}"
                )
            else:
                # Si no se puede determinar el rol, usar plantilla de jefe de seguridad por defecto
                template = HpsTemplate.objects.filter(
                    active=True,
                    template_type=HpsTemplate.TemplateType.JEFE
                ).first()
                logger.warning(
                    f"No se pudo determinar el rol del solicitante ({requested_by_role}), "
                    f"usando plantilla de jefe de seguridad por defecto. Email del token: {token.email}"
                )
            
            if not template:
                logger.warning(
                    f"No se encontró plantilla activa para traspaso HPS. "
                    f"Se requiere una plantilla de tipo 'jefe_seguridad' o 'jefe_seguridad_suplente' activa. "
                    f"Email del token: {token.email}, form_type: {form_type}, rol solicitante: {requested_by_role}"
                )
            else:
                logger.info(
                    f"Plantilla '{template.name}' (tipo: {template.template_type}) asociada a traspaso HPS. "
                    f"Email: {token.email}, solicitante: {requested_by_user.email} ({requested_by_role})"
                )
        else:
            # Para solicitudes normales, buscar cualquier plantilla activa
            template = HpsTemplate.objects.filter(active=True).first()
            if not template:
                logger.warning(
                    f"No se encontró plantilla activa para solicitud HPS. "
                    f"Email del token: {token.email}, form_type: {form_type}"
                )
        
        # Crear la solicitud HPS con el usuario correcto, request_type y template
        hps_request: HpsRequest = serializer.save(
            user=user,
            submitted_by=user,
            form_type=form_type,
            request_type=request_type,
            template=template,
        )
        HpsTokenService.mark_used(token)

        # Si es un traspaso y tiene plantilla, generar el PDF rellenado automáticamente
        if form_type == "traslado" and template and template.template_pdf:
            try:
                HpsRequestService.generate_filled_pdf(hps_request)
                logger.info(f"PDF rellenado generado automáticamente para traspaso HPS {hps_request.id}")
            except Exception as e:
                logger.error(f"Error generando PDF rellenado para traspaso HPS {hps_request.id}: {e}")
                # No fallar la creación de la solicitud si el PDF no se puede generar

        # Enviar email con credenciales si el email coincide y el usuario fue creado
        if form_email == token.email and user_created and temp_password:
            # Obtener nombre completo del usuario
            user_name = f"{user.first_name} {user.last_name}".strip() or user.email.split('@')[0].replace('.', ' ').title()
            
            send_hps_credentials_email.delay(
                {
                    "to": token.email,
                    "username": user.username,
                    "password": temp_password,  # Incluir la contraseña temporal generada
                    "user_name": user_name,
                    "request": str(hps_request.id),
                    "form_type": form_type,
                }
            )

        return hps_request

    @staticmethod
    def approve(hps_request: HpsRequest, user, expires_at=None, notes=""):
        old_status = hps_request.status
        hps_request.approve(user, expires_at)
        if notes:
            hps_request.notes = notes
        hps_request.save()
        
        # Enviar email de actualización de estado (convertir estado a string)
        email_service.send_hps_status_update_email(
            hps_request, 
            new_status=str(hps_request.status),  # Convertir a string
            old_status=str(old_status) if old_status else None  # Convertir a string
        )
        
        return hps_request

    @staticmethod
    def reject(hps_request: HpsRequest, user, notes=""):
        old_status = hps_request.status
        hps_request.reject(user, notes)
        hps_request.save()
        
        # Enviar email de actualización de estado (convertir estado a string)
        email_service.send_hps_status_update_email(
            hps_request, 
            new_status=str(hps_request.status),  # Convertir a string
            old_status=str(old_status) if old_status else None  # Convertir a string
        )
        
        return hps_request
    
    @staticmethod
    def generate_filled_pdf(hps_request: HpsRequest) -> bool:
        """
        Generar PDF rellenado automáticamente desde la plantilla y los datos de la solicitud.
        
        Args:
            hps_request: Solicitud HPS con template y datos
            
        Returns:
            True si se generó correctamente, False en caso contrario
        """
        if not hps_request.template or not hps_request.template.template_pdf:
            logger.warning(f"No hay plantilla asociada para generar PDF en solicitud {hps_request.id}")
            return False
        
        try:
            import fitz  # PyMuPDF
            
            # Abrir la plantilla PDF
            template_path = hps_request.template.template_pdf.path
            if not os.path.exists(template_path):
                logger.error(f"Archivo de plantilla no encontrado: {template_path}")
                return False
            
            # Abrir el PDF de la plantilla
            pdf_document = fitz.open(template_path)
            
            # Obtener la primera página (asumimos que el formulario está en la primera página)
            page = pdf_document[0]
            
            # Mapeo de campos del formulario a los datos de la solicitud
            # Incluimos variaciones de nombres de campos que pueden aparecer en el PDF
            field_mapping = {
                # Nombre - múltiples variaciones
                'Nombre': hps_request.first_name or '',
                'nombre': hps_request.first_name or '',
                'NOMBRE': hps_request.first_name or '',
                
                # Apellidos - múltiples variaciones
                'Apellidos': f"{hps_request.first_last_name} {hps_request.second_last_name}".strip(),
                'apellidos': f"{hps_request.first_last_name} {hps_request.second_last_name}".strip(),
                'APELLIDOS': f"{hps_request.first_last_name} {hps_request.second_last_name}".strip(),
                
                # DNI/NIE - múltiples variaciones
                'DNI': hps_request.document_number or '',
                'dni': hps_request.document_number or '',
                'NIE': hps_request.document_number or '',
                'nie': hps_request.document_number or '',
                'Documento': hps_request.document_number or '',
                'documento': hps_request.document_number or '',
                
                # Fecha de nacimiento - múltiples variaciones
                'Fecha de nacimiento': hps_request.birth_date.strftime('%d/%m/%Y') if hps_request.birth_date else '',
                'fecha de nacimiento': hps_request.birth_date.strftime('%d/%m/%Y') if hps_request.birth_date else '',
                'Fecha nacimiento': hps_request.birth_date.strftime('%d/%m/%Y') if hps_request.birth_date else '',
                'fecha nacimiento': hps_request.birth_date.strftime('%d/%m/%Y') if hps_request.birth_date else '',
                
                # Nacionalidad - múltiples variaciones
                'Nacionalidad': hps_request.nationality or '',
                'nacionalidad': hps_request.nationality or '',
                'NACIONALIDAD': hps_request.nationality or '',
                
                # Lugar de nacimiento - múltiples variaciones (IMPORTANTE: incluir todas las posibles)
                'Lugar de nacimiento': hps_request.birth_place or '',
                'lugar de nacimiento': hps_request.birth_place or '',
                'Lugar nacimiento': hps_request.birth_place or '',
                'lugar nacimiento': hps_request.birth_place or '',
                'LugarNacimiento': hps_request.birth_place or '',
                'lugarNacimiento': hps_request.birth_place or '',
                'Lugar de Nacimiento': hps_request.birth_place or '',
                'LUGAR DE NACIMIENTO': hps_request.birth_place or '',
                
                # Teléfono - múltiples variaciones
                'Teléfono': hps_request.phone or '',
                'teléfono': hps_request.phone or '',
                'telefono': hps_request.phone or '',
                'Teléfono contacto': hps_request.phone or '',
                'telefono contacto': hps_request.phone or '',
                
                # Email - múltiples variaciones
                'Email': hps_request.email or '',
                'email': hps_request.email or '',
                'EMAIL': hps_request.email or '',
                'Correo': hps_request.email or '',
                'correo': hps_request.email or '',
            }
            
            # Obtener todos los widgets del PDF
            widgets = page.widgets()
            widgets_list = list(widgets)
            
            # Buscar y rellenar campos en el PDF
            # Intentar múltiples estrategias de búsqueda
            filled_fields = set()  # Para evitar rellenar el mismo campo múltiples veces
            
            for field_name, field_value in field_mapping.items():
                if not field_value or field_name in filled_fields:
                    continue
                
                # Estrategia 1: Búsqueda exacta por nombre de campo
                for widget in widgets_list:
                    if widget.field_name:
                        widget_name_lower = widget.field_name.lower().strip()
                        field_name_lower = field_name.lower().strip()
                        
                        # Coincidencia exacta
                        if widget_name_lower == field_name_lower:
                            try:
                                widget.field_value = str(field_value)
                                widget.update()
                                filled_fields.add(field_name)
                                logger.info(f"Campo '{widget.field_name}' rellenado con '{field_value}' (coincidencia exacta)")
                                break
                            except Exception as e:
                                logger.warning(f"Error rellenando campo '{widget.field_name}': {e}")
                
                # Estrategia 2: Búsqueda parcial si no se encontró coincidencia exacta
                if field_name not in filled_fields:
                    for widget in widgets_list:
                        if widget.field_name:
                            widget_name_lower = widget.field_name.lower().strip()
                            field_name_lower = field_name.lower().strip()
                            
                            # Coincidencia parcial (el nombre del campo contiene o está contenido en el nombre del widget)
                            if (field_name_lower in widget_name_lower or 
                                widget_name_lower in field_name_lower or
                                any(word in widget_name_lower for word in field_name_lower.split() if len(word) > 3)):
                                try:
                                    widget.field_value = str(field_value)
                                    widget.update()
                                    filled_fields.add(field_name)
                                    logger.info(f"Campo '{widget.field_name}' rellenado con '{field_value}' (coincidencia parcial)")
                                    break
                                except Exception as e:
                                    logger.warning(f"Error rellenando campo '{widget.field_name}': {e}")
            
            # Los widgets ya se actualizaron con widget.update(), no necesitamos page.update()
            
            # Guardar el PDF rellenado
            pdf_bytes = pdf_document.tobytes()
            pdf_document.close()
            
            # Guardar en el campo filled_pdf
            filename = f"hps_request_{hps_request.id}_filled.pdf"
            hps_request.filled_pdf.save(
                filename,
                ContentFile(pdf_bytes),
                save=True
            )
            
            logger.info(f"PDF rellenado generado y guardado para solicitud {hps_request.id}")
            return True
            
        except ImportError:
            logger.error("PyMuPDF (fitz) no está instalado. No se puede generar PDF automáticamente.")
            return False
        except Exception as e:
            logger.error(f"Error generando PDF rellenado para solicitud {hps_request.id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

