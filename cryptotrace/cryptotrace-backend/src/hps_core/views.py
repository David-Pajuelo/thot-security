import logging
from datetime import datetime

from django.db.models import Count, Q
from django.http import FileResponse
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)

from . import models, serializers
from .permissions import HasHpsProfile, IsHpsAdmin, IsHpsAdminOrSelf, IsHpsAdminOrTeamLead, IsHpsAdminOrSecurityChief
from .services import HpsRequestService
from .extension_service import ExtensionService
from django.http import FileResponse, Http404
import re


ADMIN_ROLES = {"admin", "jefe_seguridad", "security_chief"}
TEAM_ROLES = {"team_lead", "team_leader", "jefe_seguridad_suplente"}


def is_user_team_lead(user):
    """
    Verificar si un usuario es líder de algún equipo activo.
    Esto permite que usuarios con otros roles (crypto, admin, etc.) 
    tengan permisos de líder si son líderes de un equipo.
    """
    if not user or not user.is_authenticated:
        return False
    return models.HpsTeam.objects.filter(team_lead=user, is_active=True).exists()


def has_team_lead_permissions(user, profile=None):
    """
    Verificar si un usuario tiene permisos de líder de equipo.
    Esto incluye:
    - Usuarios con rol en TEAM_ROLES
    - Usuarios que son líderes de algún equipo activo (independientemente de su rol)
    """
    if not profile:
        profile = getattr(user, "hps_profile", None)
    if not profile:
        return False
    
    role_name = profile.role.name if profile.role else None
    
    # Verificar si tiene rol de líder
    if role_name in TEAM_ROLES:
        return True
    
    # Verificar si es líder de algún equipo activo
    return is_user_team_lead(user)


class HpsRoleViewSet(viewsets.ModelViewSet):
    queryset = models.HpsRole.objects.all()
    serializer_class = serializers.HpsRoleSerializer
    permission_classes = [permissions.IsAuthenticated, IsHpsAdmin]


class HpsTeamViewSet(viewsets.ModelViewSet):
    queryset = models.HpsTeam.objects.prefetch_related("memberships")
    serializer_class = serializers.HpsTeamSerializer
    permission_classes = [permissions.IsAuthenticated, IsHpsAdminOrTeamLead]

    def get_queryset(self):
        """
        Filtrar equipos: por defecto solo mostrar activos, a menos que se solicite explícitamente
        """
        qs = super().get_queryset()
        # Si no se especifica 'include_inactive', solo mostrar equipos activos
        include_inactive = self.request.query_params.get('include_inactive', 'false').lower() == 'true'
        if not include_inactive:
            qs = qs.filter(is_active=True)
        return qs

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """
        Obtener estadísticas de equipos
        GET /api/hps/teams/stats/
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Total de equipos
        total_teams = models.HpsTeam.objects.count()
        
        # Equipos activos
        active_teams = models.HpsTeam.objects.filter(is_active=True).count()
        
        # Total de miembros (usuarios con perfil HPS activo)
        total_members = models.HpsUserProfile.objects.filter(
            user__is_active=True
        ).count()
        
        # Equipos con líderes asignados
        teams_with_leaders = models.HpsTeam.objects.filter(
            is_active=True,
            team_lead__isnull=False
        ).count()
        
        return Response({
            'total_teams': total_teams,
            'active_teams': active_teams,
            'total_members': total_members,
            'teams_with_leaders': teams_with_leaders
        })

    @action(detail=True, methods=["get"], url_path="members")
    def members(self, request, pk=None):
        """
        Obtener miembros de un equipo
        GET /api/hps/teams/{id}/members/
        """
        team = self.get_object()
        
        # Obtener todos los usuarios que pertenecen a este equipo a través de HpsUserProfile
        members = models.HpsUserProfile.objects.filter(
            team=team,
            user__is_active=True
        ).select_related('user', 'role')
        
        # Formatear respuesta para el frontend
        members_list = []
        for profile in members:
            members_list.append({
                'id': profile.user.id,
                'email': profile.user.email,
                'full_name': f"{profile.user.first_name} {profile.user.last_name}".strip() or profile.user.email,
                'first_name': profile.user.first_name,
                'last_name': profile.user.last_name,
                'role': profile.role.name if profile.role else None,
                'is_active': profile.user.is_active
            })
        
        return Response(members_list)


class HpsRequestViewSet(viewsets.ModelViewSet):
    queryset = models.HpsRequest.objects.select_related(
        "user", "submitted_by", "approved_by", "template"
    )
    serializer_class = serializers.HpsRequestSerializer
    permission_classes = [permissions.IsAuthenticated, HasHpsProfile]

    def _profile(self):
        user = self.request.user
        return getattr(user, "hps_profile", None)
    
    def get_serializer_context(self):
        """Añadir request al contexto para generar URLs absolutas"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get("status")
        request_type = self.request.query_params.get("request_type")
        form_type = self.request.query_params.get("form_type") or self.request.query_params.get("hps_type")  # Aceptar ambos
        user_id = self.request.query_params.get("user_id")
        team_id = self.request.query_params.get("team_id")

        if status_param:
            qs = qs.filter(status=status_param)
        if request_type:
            qs = qs.filter(request_type=request_type)
        if form_type:
            qs = qs.filter(form_type=form_type)
        if user_id:
            qs = qs.filter(user_id=user_id)
        if team_id:
            qs = qs.filter(user__hps_profile__team_id=team_id)

        profile = self._profile()
        if not profile:
            return qs.none()

        role_name = profile.role.name if profile.role else None
        if role_name in ADMIN_ROLES:
            return qs

        # Verificar si tiene permisos de líder (rol o es líder de equipo)
        if has_team_lead_permissions(self.request.user, profile) and profile.team_id:
            return qs.filter(user__hps_profile__team_id=profile.team_id)

        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        default_user = serializer.validated_data.get("user") or self.request.user
        serializer.save(
            user=default_user,
            submitted_by=serializer.validated_data.get("submitted_by", self.request.user),
        )

    @action(detail=False, methods=["get"], url_path="team/(?P<team_id>[^/.]+)")
    def team_requests(self, request, team_id=None):
        qs = self.get_queryset().filter(user__hps_profile__team_id=team_id)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        qs = self.get_queryset()
        # El modelo no tiene WAITING_DPS, así que devolvemos 0 para ese estado
        data = qs.aggregate(
            total_requests=Count("id"),
            pending_requests=Count("id", filter=Q(status=models.HpsRequest.RequestStatus.PENDING)),
            waiting_dps_requests=Count("id", filter=Q(status=models.HpsRequest.RequestStatus.WAITING_DPS)),
            submitted_requests=Count("id", filter=Q(status=models.HpsRequest.RequestStatus.SUBMITTED)),
            approved_requests=Count("id", filter=Q(status=models.HpsRequest.RequestStatus.APPROVED)),
            rejected_requests=Count("id", filter=Q(status=models.HpsRequest.RequestStatus.REJECTED)),
            expired_requests=Count("id", filter=Q(status=models.HpsRequest.RequestStatus.EXPIRED)),
        )
        return Response(data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        hps_request = self.get_object()
        expires_at = request.data.get("expires_at")
        notes = request.data.get("notes", "")

        if hps_request.status != models.HpsRequest.RequestStatus.PENDING:
            return Response(
                {"detail": "La solicitud no se puede aprobar en su estado actual."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expires_date = None
        if expires_at:
            expires_date = datetime.fromisoformat(expires_at).date()

        hps_request = HpsRequestService.approve(
            hps_request, request.user, expires_date, notes
        )
        return Response(self.get_serializer(hps_request).data)

    @action(detail=True, methods=["get"], url_path="filled-pdf")
    def filled_pdf(self, request, pk=None):
        """
        Obtener PDF rellenado de una solicitud HPS
        GET /api/hps/requests/{id}/filled-pdf/
        """
        hps_request = self.get_object()
        
        if not hps_request.filled_pdf:
            return Response(
                {'detail': 'No hay PDF rellenado para esta solicitud'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            from django.http import FileResponse
            import re
            
            # Generar nombre del archivo
            user_name = f"{hps_request.first_name} {hps_request.first_last_name}".strip()
            if hps_request.second_last_name:
                user_name += f" {hps_request.second_last_name}"
            
            # Limpiar caracteres no válidos
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', user_name)
            filename = f"{safe_name} - HPS Filled.pdf"
            
            return FileResponse(
                hps_request.filled_pdf.open('rb'),
                content_type='application/pdf',
                filename=filename,
                as_attachment=False  # Mostrar en navegador, no descargar
            )
        except Exception as e:
            logger.error(f"Error obteniendo PDF rellenado: {e}")
            return Response(
                {'detail': f'Error obteniendo PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=["get"], url_path="response-pdf")
    def response_pdf(self, request, pk=None):
        """
        Obtener PDF de respuesta de una solicitud HPS
        GET /api/hps/requests/{id}/response-pdf/
        """
        hps_request = self.get_object()
        
        if not hps_request.response_pdf:
            return Response(
                {'detail': 'No hay PDF de respuesta para esta solicitud'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            from django.http import FileResponse
            import re
            
            # Generar nombre del archivo
            user_name = f"{hps_request.first_name} {hps_request.first_last_name}".strip()
            if hps_request.second_last_name:
                user_name += f" {hps_request.second_last_name}"
            
            # Limpiar caracteres no válidos
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', user_name)
            filename = f"{safe_name} - HPS Response.pdf"
            
            return FileResponse(
                hps_request.response_pdf.open('rb'),
                content_type='application/pdf',
                filename=filename,
                as_attachment=False  # Mostrar en navegador, no descargar
            )
        except Exception as e:
            logger.error(f"Error obteniendo PDF de respuesta: {e}")
            return Response(
                {'detail': f'Error obteniendo PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """Marcar solicitud como enviada (cambiar estado a 'submitted')"""
        hps_request = self.get_object()
        notes = request.data.get("notes", "")

        if hps_request.status != models.HpsRequest.RequestStatus.PENDING:
            return Response(
                {"detail": "La solicitud no se puede enviar en su estado actual."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = hps_request.status
        hps_request.status = models.HpsRequest.RequestStatus.SUBMITTED
        hps_request.submitted_at = datetime.now()
        hps_request.submitted_by = request.user
        if notes:
            # Guardar notas en algún campo si existe, o crear un audit log
            pass
        hps_request.save()
        
        # Enviar email de actualización de estado (convertir estado a string)
        from .email_service import HpsEmailService
        email_service = HpsEmailService()
        email_service.send_hps_status_update_email(
            hps_request,
            new_status=str(hps_request.status),  # Convertir a string
            old_status=str(old_status) if old_status else None  # Convertir a string
        )

        return Response(self.get_serializer(hps_request).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        hps_request = self.get_object()
        notes = request.data.get("notes", "")

        if hps_request.status != models.HpsRequest.RequestStatus.PENDING:
            return Response(
                {"detail": "La solicitud no se puede rechazar en su estado actual."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        hps_request = HpsRequestService.reject(hps_request, request.user, notes)
        return Response(self.get_serializer(hps_request).data)
    
    @action(detail=True, methods=["get"], url_path="extract-pdf-fields")
    def extract_pdf_fields(self, request, pk=None):
        """
        Extraer campos del PDF rellenado usando PyMuPDF
        GET /api/hps/requests/{id}/extract-pdf-fields/
        """
        hps_request = self.get_object()
        
        if not hps_request.filled_pdf:
            return Response(
                {'detail': 'No hay PDF rellenado para esta solicitud'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            import fitz  # PyMuPDF
            import os
            
            # Abrir el PDF rellenado
            pdf_path = hps_request.filled_pdf.path
            if not os.path.exists(pdf_path):
                return Response(
                    {'detail': 'Archivo PDF no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            pdf_document = fitz.open(pdf_path)
            page = pdf_document[0]
            
            # Extraer campos del formulario
            extracted_fields = {}
            widgets = page.widgets()
            
            for widget in widgets:
                if widget.field_name and widget.field_value:
                    field_name = widget.field_name.strip()
                    field_value = str(widget.field_value).strip()
                    if field_value:
                        extracted_fields[field_name] = field_value
            
            # Si no hay campos de formulario, intentar extraer texto
            if not extracted_fields:
                # Extraer texto de la página
                text_dict = page.get_text("dict")
                # Buscar patrones comunes en el texto
                full_text = page.get_text()
                
                # Mapeo de patrones para extraer valores
                patterns = {
                    'Nombre': r'(?:Nombre|NOMBRE)[:\s]*([^\n\r,]+)',
                    'Apellidos': r'(?:Apellidos|APELLIDOS)[:\s]*([^\n\r,]+)',
                    'DNI': r'(?:DNI|NIE)[:\s]*([A-Z0-9]{8,9})',
                    'Fecha de nacimiento': r'(?:Fecha de nacimiento|Fecha nacimiento)[:\s]*([^\n\r,]+)',
                    'Nacionalidad': r'(?:Nacionalidad|NACIONALIDAD)[:\s]*([^\n\r,]+)',
                    'Lugar de nacimiento': r'(?:Lugar de nacimiento|Lugar nacimiento|LugarNacimiento)[:\s]*([^\n\r,]+)',
                    'Teléfono': r'(?:Teléfono|Telefono|TELÉFONO)[:\s]*([^\n\r,]+)',
                    'Email': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                }
                
                import re
                for field_name, pattern in patterns.items():
                    match = re.search(pattern, full_text, re.IGNORECASE)
                    if match:
                        extracted_fields[field_name] = match.group(1).strip()
            
            pdf_document.close()
            
            return Response(extracted_fields, status=status.HTTP_200_OK)
            
        except ImportError:
            return Response(
                {'detail': 'PyMuPDF no está instalado. No se pueden extraer campos del PDF.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Error extrayendo campos del PDF: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'detail': f'Error extrayendo campos: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=["post"], url_path="edit-filled-pdf")
    def edit_filled_pdf(self, request, pk=None):
        """
        Editar campos del PDF rellenado
        POST /api/hps/requests/{id}/edit-filled-pdf/
        Body: { "Nombre": "valor", "Apellidos": "valor", ... }
        """
        hps_request = self.get_object()
        
        if not hps_request.filled_pdf:
            return Response(
                {'detail': 'No hay PDF rellenado para esta solicitud'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        field_updates = request.data
        if not field_updates or not isinstance(field_updates, dict):
            return Response(
                {'detail': 'Se requieren campos para actualizar'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            import fitz  # PyMuPDF
            import os
            import io
            from django.core.files.base import ContentFile
            
            # Abrir el PDF rellenado desde el almacenamiento de Django
            with hps_request.filled_pdf.open('rb') as f:
                pdf_bytes_original = f.read()
            
            # Crear documento desde bytes en memoria
            pdf_document = fitz.open(stream=pdf_bytes_original, filetype="pdf")
            page = pdf_document[0]
            
            # Obtener widgets y actualizar valores
            widgets = list(page.widgets())  # Convertir a lista para iterar correctamente
            updated_count = 0
            updated_fields = []
            
            for field_name, field_value in field_updates.items():
                if not field_value:
                    continue
                
                field_name_lower = field_name.lower().strip()
                field_value_str = str(field_value).strip()
                
                # Buscar el widget correspondiente
                found = False
                for widget in widgets:
                    if widget.field_name:
                        widget_name_lower = widget.field_name.lower().strip()
                        
                        # Coincidencia exacta o parcial
                        if (widget_name_lower == field_name_lower or 
                            field_name_lower in widget_name_lower or
                            widget_name_lower in field_name_lower):
                            try:
                                widget.field_value = field_value_str
                                widget.update()
                                updated_count += 1
                                updated_fields.append(widget.field_name)
                                logger.info(f"Campo '{widget.field_name}' actualizado con '{field_value_str}'")
                                found = True
                                break
                            except Exception as e:
                                logger.warning(f"Error actualizando campo '{widget.field_name}': {e}")
                
                if not found:
                    logger.warning(f"No se encontró widget para el campo '{field_name}'")
            
            # Guardar el PDF actualizado en un buffer en memoria
            output_buffer = io.BytesIO()
            pdf_document.save(output_buffer)
            pdf_document.close()
            
            # Obtener los bytes del PDF actualizado
            pdf_bytes = output_buffer.getvalue()
            output_buffer.close()
            
            # Eliminar el archivo anterior si existe para evitar problemas de caché
            if hps_request.filled_pdf:
                try:
                    old_path = hps_request.filled_pdf.path
                    if os.path.exists(old_path):
                        os.remove(old_path)
                        logger.debug(f"Archivo PDF anterior eliminado: {old_path}")
                except Exception as e:
                    logger.warning(f"No se pudo eliminar el archivo PDF anterior: {e}")
            
            # Guardar el nuevo PDF
            filename = f"hps_request_{hps_request.id}_filled.pdf"
            hps_request.filled_pdf.save(
                filename,
                ContentFile(pdf_bytes),
                save=True  # Guardar el modelo automáticamente
            )
            
            # Forzar actualización del timestamp
            hps_request.save(update_fields=['updated_at'])
            
            logger.info(f"PDF actualizado para solicitud {hps_request.id} ({updated_count} campos actualizados: {updated_fields})")
            
            return Response({
                'detail': f'PDF actualizado correctamente ({updated_count} campos actualizados)',
                'updated_fields': updated_count,
                'field_names': updated_fields,
                'success': True
            }, status=status.HTTP_200_OK)
            
        except ImportError:
            return Response(
                {'detail': 'PyMuPDF no está instalado. No se puede editar el PDF.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Error editando PDF: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'detail': f'Error editando PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"], url_path="pending/list")
    def pending(self, request):
        qs = self.get_queryset().filter(status=models.HpsRequest.RequestStatus.PENDING)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="submitted/list")
    def submitted(self, request):
        qs = self.get_queryset().filter(
            status__in=[
                models.HpsRequest.RequestStatus.APPROVED,
                models.HpsRequest.RequestStatus.REJECTED,
            ]
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="public", permission_classes=[permissions.AllowAny])
    def create_public(self, request):
        token_value = request.query_params.get("token")
        # Aceptar tanto form_type como hps_type (compatibilidad con frontend)
        raw_form_type = request.query_params.get("form_type") or request.query_params.get("hps_type", "solicitud")
        
        # Normalizar form_type: debe ser "solicitud" o "traslado"
        # Si viene como "nueva", "new", etc., convertir a "solicitud"
        form_type_lower = raw_form_type.lower().strip()
        if form_type_lower in ["traslado", "traspaso", "transfer", "trasladar", "traspasar"]:
            form_type = "traslado"
        else:
            # Por defecto, cualquier otro valor (incluyendo "nueva", "new", "solicitud", etc.) se convierte a "solicitud"
            form_type = "solicitud"
        
        if not token_value:
            return Response(
                {"detail": "Token requerido."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = models.HpsToken.objects.get(token=token_value)
        except models.HpsToken.DoesNotExist:
            return Response(
                {"detail": "Token inválido o expirado."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not token.is_valid:
            return Response(
                {"detail": "Token expirado o ya utilizado."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Crear serializer con datos del request, excluyendo user y submitted_by que se asignarán automáticamente
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Error de validación del serializer: {serializer.errors}")
            return Response(
                {"detail": "Error de validación", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            hps_request = HpsRequestService.create_from_token(
                serializer=serializer,
                token=token,
                form_type=form_type,
            )
            return Response(
                self.get_serializer(hps_request).data, status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error creando solicitud HPS desde token: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {"detail": f"Error al crear la solicitud: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HpsTokenViewSet(viewsets.ModelViewSet):
    queryset = models.HpsToken.objects.all()
    serializer_class = serializers.HpsTokenSerializer
    permission_classes = [permissions.IsAuthenticated, HasHpsProfile]
    
    def get_permissions(self):
        """
        Solo admins y jefes de seguridad (incluyendo suplentes) pueden crear tokens.
        La validación de tokens es pública.
        """
        if self.action == 'create':
            # Para crear tokens, se requiere ser admin o jefe de seguridad (incluyendo suplentes)
            return [permissions.IsAuthenticated(), IsHpsAdminOrSecurityChief()]
        elif self.action == 'validate_token':
            # La validación de tokens es pública (AllowAny)
            return [permissions.AllowAny()]
        else:
            # Para otras acciones (list, retrieve, etc.), se requiere ser admin
            return [permissions.IsAuthenticated(), IsHpsAdmin()]
    
    def perform_create(self, serializer):
        """Crear token HPS usando el método del modelo que genera automáticamente token y expires_at"""
        email = serializer.validated_data.get('email')
        purpose = serializer.validated_data.get('purpose', '')
        hours_valid = serializer.validated_data.get('hours_valid', 72)
        
        # Usar el método del modelo que genera automáticamente token y expires_at
        token = models.HpsToken.create_token(
            email=email,
            requested_by_user=self.request.user,
            purpose=purpose,
            hours_valid=hours_valid
        )
        
        # Actualizar el serializer con el token creado
        serializer.instance = token
    
    @action(detail=False, methods=['get'], url_path='validate')
    def validate_token(self, request):
        """
        Validar un token HPS (endpoint público)
        GET /api/hps/tokens/validate/?token=xxx&email=xxx
        """
        token_value = request.query_params.get('token')
        email_param = request.query_params.get('email')
        
        if not token_value:
            return Response(
                {'detail': 'Token requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            token = models.HpsToken.objects.get(token=token_value)
        except models.HpsToken.DoesNotExist:
            return Response(
                {'detail': 'Token inválido o expirado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validar que el token sea válido
        if not token.is_valid:
            return Response(
                {
                    'detail': 'Token expirado o ya utilizado',
                    'is_valid': False,
                    'is_expired': token.is_expired,
                    'is_used': token.is_used
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Si se proporciona email, validar que coincida
        if email_param and email_param.lower() != token.email.lower():
            return Response(
                {'detail': 'El email no coincide con el token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'is_valid': True,
            'email': token.email,
            'expires_at': token.expires_at.isoformat(),
            'purpose': token.purpose
        }, status=status.HTTP_200_OK)


class HpsTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar plantillas PDF de HPS"""
    queryset = models.HpsTemplate.objects.all()
    serializer_class = serializers.HpsTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsHpsAdmin]
    
    def get_serializer_context(self):
        """Añadir request al contexto para generar URLs absolutas"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def list(self, request, *args, **kwargs):
        """
        Sobrescribir list para devolver formato compatible con el frontend
        El frontend espera: { templates: [...], total: N }
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Aplicar paginación si se solicita
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            total = queryset.count()
            return Response({
                'templates': serializer.data,
                'total': total,
                'page': int(request.query_params.get('page', 1)),
                'per_page': int(request.query_params.get('per_page', 10))
            })
        
        # Sin paginación, devolver todas las plantillas
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'templates': serializer.data,
            'total': queryset.count()
        })
    
    def perform_create(self, serializer):
        """
        Guardar plantilla y verificar que el archivo se guardó correctamente.
        Si la plantilla se marca como activa, eliminar la plantilla anterior activa del mismo tipo.
        """
        try:
            template = serializer.save()
            
            # Si la plantilla se marca como activa, eliminar la plantilla anterior activa del mismo tipo
            if template.active:
                old_templates = models.HpsTemplate.objects.filter(
                    template_type=template.template_type,
                    active=True
                ).exclude(id=template.id)
                
                for old_template in old_templates:
                    # Eliminar el archivo PDF asociado si existe
                    if old_template.template_pdf:
                        try:
                            import os
                            from django.conf import settings
                            file_path = os.path.join(settings.MEDIA_ROOT, old_template.template_pdf.name)
                            if os.path.exists(file_path):
                                os.remove(file_path)
                                logger.info(f"Archivo PDF eliminado: {file_path}")
                        except Exception as e:
                            logger.warning(f"Error al eliminar archivo PDF de plantilla anterior: {e}")
                    
                    # Eliminar la plantilla de la base de datos
                    old_template.delete()
                    logger.info(f"Plantilla anterior '{old_template.name}' (ID: {old_template.id}) eliminada para tipo {template.template_type}")
                
                if old_templates.exists():
                    logger.info(f"Plantilla {template.name} creada. {old_templates.count()} plantilla(s) anterior(es) de tipo {template.template_type} eliminada(s).")
            
            # Verificar que el archivo PDF se guardó
            if template.template_pdf:
                import os
                from django.conf import settings
                file_path = os.path.join(settings.MEDIA_ROOT, template.template_pdf.name)
                if os.path.exists(file_path):
                    logger.info(f"Plantilla {template.name} creada correctamente. PDF guardado en: {file_path}")
                else:
                    logger.warning(f"Plantilla {template.name} creada pero el archivo PDF no se encontró en: {file_path}")
            else:
                logger.warning(f"Plantilla {template.name} creada sin archivo PDF")
        except Exception as e:
            logger.error(f"Error al crear plantilla: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def perform_update(self, serializer):
        """
        Actualizar plantilla. Si se marca como activa, eliminar otras plantillas activas del mismo tipo.
        """
        try:
            template = serializer.save()
            
            # Si la plantilla se marca como activa, eliminar otras plantillas activas del mismo tipo
            if template.active:
                old_templates = models.HpsTemplate.objects.filter(
                    template_type=template.template_type,
                    active=True
                ).exclude(id=template.id)
                
                for old_template in old_templates:
                    # Eliminar el archivo PDF asociado si existe
                    if old_template.template_pdf:
                        try:
                            import os
                            from django.conf import settings
                            file_path = os.path.join(settings.MEDIA_ROOT, old_template.template_pdf.name)
                            if os.path.exists(file_path):
                                os.remove(file_path)
                                logger.info(f"Archivo PDF eliminado: {file_path}")
                        except Exception as e:
                            logger.warning(f"Error al eliminar archivo PDF de plantilla anterior: {e}")
                    
                    # Eliminar la plantilla de la base de datos
                    old_template.delete()
                    logger.info(f"Plantilla anterior '{old_template.name}' (ID: {old_template.id}) eliminada para tipo {template.template_type}")
                
                if old_templates.exists():
                    logger.info(f"Plantilla {template.name} actualizada. {old_templates.count()} plantilla(s) anterior(es) de tipo {template.template_type} eliminada(s).")
        except Exception as e:
            logger.error(f"Error al actualizar plantilla: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    @action(detail=False, methods=['get'], url_path='active')
    def active_templates(self, request):
        """Obtener solo las plantillas activas"""
        active_templates = self.get_queryset().filter(active=True)
        serializer = self.get_serializer(active_templates, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='by-type/(?P<template_type>[^/.]+)')
    def by_type(self, request, template_type=None):
        """Obtener plantillas por tipo (jefe_seguridad o jefe_seguridad_suplente)"""
        templates = self.get_queryset().filter(
            template_type=template_type,
            active=True
        )
        serializer = self.get_serializer(templates, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=["get"], url_path="extract-pdf-fields")
    def extract_pdf_fields(self, request, pk=None):
        """
        Extraer campos del PDF de la plantilla usando PyMuPDF
        GET /api/hps/templates/{id}/extract-pdf-fields/
        """
        template = self.get_object()
        
        if not template.template_pdf:
            return Response(
                {'detail': 'No hay PDF para esta plantilla'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            import fitz  # PyMuPDF
            import os
            
            # Abrir el PDF de la plantilla
            pdf_path = template.template_pdf.path
            if not os.path.exists(pdf_path):
                return Response(
                    {'detail': 'Archivo PDF no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            pdf_document = fitz.open(pdf_path)
            page = pdf_document[0]
            
            # Extraer campos del formulario
            extracted_fields = {}
            widgets = page.widgets()
            
            for widget in widgets:
                if widget.field_name and widget.field_value:
                    field_name = widget.field_name.strip()
                    field_value = str(widget.field_value).strip()
                    if field_value:
                        extracted_fields[field_name] = field_value
            
            # Si no hay campos de formulario, intentar extraer texto
            if not extracted_fields:
                # Extraer texto de la página
                full_text = page.get_text()
                
                # Mapeo de patrones para extraer valores (campos específicos de plantillas)
                patterns = {
                    'Identificación': r'(?:Identificación|IDENTIFICACIÓN|DNI|NIE)[:\s]*([^\n\r,]+)',
                    'Correo electrónico_2': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                    'Teléfono_2': r'(?:Teléfono|Telefono|TELÉFONO)[:\s]*([^\n\r,]+)',
                }
                
                import re
                for field_name, pattern in patterns.items():
                    match = re.search(pattern, full_text, re.IGNORECASE)
                    if match:
                        extracted_fields[field_name] = match.group(1).strip()
            
            pdf_document.close()
            
            return Response(extracted_fields, status=status.HTTP_200_OK)
            
        except ImportError:
            return Response(
                {'detail': 'PyMuPDF no está instalado. No se pueden extraer campos del PDF.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Error extrayendo campos del PDF de plantilla: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'detail': f'Error extrayendo campos: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=["post"], url_path="edit-pdf")
    def edit_pdf(self, request, pk=None):
        """
        Editar campos del PDF de la plantilla
        POST /api/hps/templates/{id}/edit-pdf/
        Body: { "Identificación": "valor", "Correo electrónico_2": "valor", ... }
        """
        template = self.get_object()
        
        if not template.template_pdf:
            return Response(
                {'detail': 'No hay PDF para esta plantilla'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        field_updates = request.data
        if not field_updates or not isinstance(field_updates, dict):
            return Response(
                {'detail': 'Se requieren campos para actualizar'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            import fitz  # PyMuPDF
            import os
            import io
            from django.core.files.base import ContentFile
            
            # Abrir el PDF de la plantilla desde el almacenamiento de Django
            with template.template_pdf.open('rb') as f:
                pdf_bytes_original = f.read()
            
            # Crear documento desde bytes en memoria
            pdf_document = fitz.open(stream=pdf_bytes_original, filetype="pdf")
            page = pdf_document[0]
            
            # Obtener widgets y actualizar valores
            widgets = list(page.widgets())  # Convertir a lista para iterar correctamente
            updated_count = 0
            updated_fields = []
            
            for field_name, field_value in field_updates.items():
                if not field_value:
                    continue
                
                field_name_lower = field_name.lower().strip()
                field_value_str = str(field_value).strip()
                
                # Buscar el widget correspondiente
                found = False
                for widget in widgets:
                    if widget.field_name:
                        widget_name_lower = widget.field_name.lower().strip()
                        
                        # Coincidencia exacta o parcial
                        if (widget_name_lower == field_name_lower or 
                            field_name_lower in widget_name_lower or
                            widget_name_lower in field_name_lower):
                            try:
                                widget.field_value = field_value_str
                                widget.update()
                                updated_count += 1
                                updated_fields.append(widget.field_name)
                                logger.info(f"Campo '{widget.field_name}' actualizado con '{field_value_str}'")
                                found = True
                                break
                            except Exception as e:
                                logger.warning(f"Error actualizando campo '{widget.field_name}': {e}")
                
                if not found:
                    logger.warning(f"No se encontró widget para el campo '{field_name}'")
            
            # Guardar el PDF actualizado en un buffer en memoria
            output_buffer = io.BytesIO()
            pdf_document.save(output_buffer)
            pdf_document.close()
            
            # Obtener los bytes del PDF actualizado
            pdf_bytes = output_buffer.getvalue()
            output_buffer.close()
            
            # Eliminar el archivo anterior si existe para evitar problemas de caché
            if template.template_pdf:
                try:
                    old_path = template.template_pdf.path
                    if os.path.exists(old_path):
                        os.remove(old_path)
                        logger.debug(f"Archivo PDF anterior eliminado: {old_path}")
                except Exception as e:
                    logger.warning(f"No se pudo eliminar el archivo PDF anterior: {e}")
            
            # Guardar el nuevo PDF
            filename = f"template_{template.id}_{template.name.replace(' ', '_')}.pdf"
            template.template_pdf.save(
                filename,
                ContentFile(pdf_bytes),
                save=True  # Guardar el modelo automáticamente
            )
            
            logger.info(f"PDF de plantilla {template.name} actualizado. {updated_count} campo(s) modificado(s): {', '.join(updated_fields)}")
            
            return Response({
                'detail': f'PDF actualizado correctamente. {updated_count} campo(s) modificado(s).',
                'updated_fields': updated_fields,
                'updated_count': updated_count
            }, status=status.HTTP_200_OK)
            
        except ImportError:
            return Response(
                {'detail': 'PyMuPDF no está instalado. No se puede editar el PDF.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Error editando PDF de plantilla: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'detail': f'Error editando PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=["get"], url_path="pdf")
    def get_pdf(self, request, pk=None):
        """
        Obtener el PDF de la plantilla como archivo binario
        GET /api/hps/templates/{id}/pdf/
        """
        template = self.get_object()
        
        if not template.template_pdf:
            return Response(
                {'detail': 'No hay PDF para esta plantilla'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            from django.http import FileResponse
            import os
            
            pdf_path = template.template_pdf.path
            if not os.path.exists(pdf_path):
                return Response(
                    {'detail': 'Archivo PDF no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return FileResponse(
                open(pdf_path, 'rb'),
                content_type='application/pdf',
                filename=os.path.basename(pdf_path)
            )
        except Exception as e:
            logger.error(f"Error obteniendo PDF de plantilla: {e}")
            return Response(
                {'detail': f'Error obteniendo PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HpsAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.HpsAuditLog.objects.select_related("user")
    serializer_class = serializers.HpsAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsHpsAdminOrSelf]


class HpsUserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar perfiles de usuario HPS
    Permite listar, ver, crear, actualizar, desactivar y eliminar usuarios
    """
    queryset = models.HpsUserProfile.objects.select_related('user', 'role', 'team')
    serializer_class = serializers.HpsUserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, HasHpsProfile]

    def get_queryset(self):
        qs = super().get_queryset()
        profile = getattr(self.request.user, "hps_profile", None)
        
        if not profile:
            return qs.none()
        
        role_name = profile.role.name if profile.role else None
        
        # Admins, jefes de seguridad y cryptos pueden ver todos los perfiles
        if role_name in ADMIN_ROLES or role_name == "crypto":
            return qs
        
        # Team leads solo pueden ver perfiles de su equipo
        # También incluye usuarios que son líderes de equipo aunque su rol no sea team_lead
        if has_team_lead_permissions(self.request.user, profile) and profile.team_id:
            return qs.filter(team_id=profile.team_id)
        
        # Otros usuarios (members) pueden ver todos los usuarios también
        # Según el requerimiento: todos los usuarios deben aparecer en la gestión
        return qs
    
    def get_permissions(self):
        """
        Solo admins pueden crear, actualizar, desactivar y eliminar usuarios
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'activate', 'deactivate', 'permanent_delete']:
            return [permissions.IsAuthenticated(), IsHpsAdmin()]
        return [permissions.IsAuthenticated(), HasHpsProfile()]
    
    def get_object(self):
        """
        Sobrescribir get_object para permitir buscar por ID de perfil o ID de usuario
        """
        lookup_value = self.kwargs.get(self.lookup_field)
        
        # Intentar buscar por ID de perfil primero
        try:
            return super().get_object()
        except Http404:
            # Si no se encuentra, intentar buscar por user_id
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=lookup_value)
                if hasattr(user, 'hps_profile'):
                    return user.hps_profile
                raise Http404("No HpsUserProfile matches the given query.")
            except (User.DoesNotExist, ValueError):
                raise Http404("No HpsUserProfile matches the given query.")
    
    def destroy(self, request, *args, **kwargs):
        """
        Sobrescribir destroy para marcar usuario como inactivo en lugar de eliminarlo
        DELETE /api/hps/user/profiles/{id}/ -> Marca como inactivo
        Acepta tanto ID de perfil como ID de usuario
        """
        try:
            profile = self.get_object()
            user = profile.user
            
            # No permitir desactivar a uno mismo
            if user.id == request.user.id:
                return Response(
                    {'detail': 'No puedes desactivarte a ti mismo'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Marcar usuario como inactivo
            user.is_active = False
            user.save()
            
            logger.info(f"Usuario {user.email} (ID: {user.id}) marcado como inactivo por {request.user.email}")
            
            serializer = self.get_serializer(profile)
            return Response({
                'message': f'Usuario {user.email} marcado como inactivo',
                **serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error desactivando usuario: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'detail': f'Error desactivando usuario: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        """
        Desactivar un usuario (marcar como inactivo)
        POST /api/hps/user/profiles/{id}/deactivate/
        Acepta tanto ID de perfil como ID de usuario
        """
        try:
            profile = self.get_object()
            user = profile.user
            
            # No permitir desactivar a uno mismo
            if user.id == request.user.id:
                return Response(
                    {'detail': 'No puedes desactivarte a ti mismo'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Marcar usuario como inactivo
            user.is_active = False
            user.save()
            
            logger.info(f"Usuario {user.email} (ID: {user.id}) marcado como inactivo por {request.user.email}")
            
            serializer = self.get_serializer(profile)
            return Response({
                'message': f'Usuario {user.email} marcado como inactivo',
                **serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error desactivando usuario: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'detail': f'Error desactivando usuario: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        """
        Activar un usuario (marcar como activo)
        POST /api/hps/user/profiles/{id}/activate/
        Acepta tanto ID de perfil como ID de usuario
        """
        try:
            profile = self.get_object()
            user = profile.user
            
            # Activar usuario
            user.is_active = True
            user.save()
            
            logger.info(f"Usuario {user.email} (ID: {user.id}) activado por {request.user.email}")
            
            serializer = self.get_serializer(profile)
            return Response({
                'message': f'Usuario {user.email} activado correctamente',
                **serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error activando usuario: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'detail': f'Error activando usuario: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['delete'], url_path='permanent')
    def permanent_delete(self, request, pk=None):
        """
        Eliminar definitivamente un usuario y su perfil HPS
        DELETE /api/hps/user/profiles/{id}/permanent/
        """
        try:
            profile = self.get_object()
            user = profile.user
            
            # No permitir eliminarse a uno mismo
            if user.id == request.user.id:
                return Response(
                    {'detail': 'No puedes eliminarte a ti mismo'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Guardar información para el log
            user_email = user.email
            user_id = user.id
            
            # Eliminar el perfil HPS primero (para evitar problemas de foreign key)
            profile.delete()
            
            # Eliminar el usuario
            user.delete()
            
            logger.info(f"Usuario {user_email} (ID: {user_id}) eliminado definitivamente por {request.user.email}")
            
            return Response({
                'message': f'Usuario {user_email} eliminado definitivamente'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error eliminando usuario: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'detail': f'Error eliminando usuario: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=["get"])
    def stats(self, request):
        """
        Obtener estadísticas de usuarios
        GET /api/hps/user/profiles/stats/
        """
        from django.contrib.auth import get_user_model
        from django.db.models import Count
        User = get_user_model()
        
        # Obtener estadísticas básicas
        total_users = models.HpsUserProfile.objects.count()
        active_users = models.HpsUserProfile.objects.filter(user__is_active=True).count()
        
        # Obtener conteo por rol
        users_by_role = models.HpsUserProfile.objects.filter(
            user__is_active=True
        ).values(
            'role__name'
        ).annotate(
            count=Count('id')
        ).order_by('role__name')
        
        # Convertir a diccionario más legible
        role_counts = {}
        for item in users_by_role:
            role_name = item['role__name'] or 'sin_rol'
            role_counts[role_name] = item['count']
        
        # Contar usuarios que son líderes de equipo (independientemente de su rol)
        team_leaders_count = models.HpsTeam.objects.filter(
            is_active=True,
            team_lead__isnull=False,
            team_lead__is_active=True
        ).count()
        
        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'users_by_role': role_counts,
            # Campos específicos para compatibilidad con el Dashboard
            'crypto': role_counts.get('crypto', 0),
            'members': role_counts.get('member', 0),
            'team_leaders': team_leaders_count,
            'admin': role_counts.get('admin', 0),
            'jefe_seguridad': role_counts.get('jefe_seguridad', 0),
            'jefe_seguridad_suplente': role_counts.get('jefe_seguridad_suplente', 0),
        })
    


class HpsExtensionViewSet(viewsets.ViewSet):
    """
    ViewSet para endpoints del complemento de navegador
    Estos endpoints NO requieren autenticación (públicos para el complemento)
    """
    permission_classes = []  # Sin autenticación requerida
    
    @action(detail=False, methods=['get'], url_path='personas')
    def get_personas_pendientes(self, request):
        """
        Obtener lista de personas con estado 'pending' para el complemento de navegador
        GET /api/v1/extension/personas?tipo=solicitud
        """
        tipo = request.query_params.get('tipo')
        personas = ExtensionService.get_personas_pendientes(tipo)
        return Response(personas, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='persona/(?P<numero_documento>[^/.]+)')
    def get_persona_por_dni(self, request, numero_documento=None):
        """
        Obtener datos detallados de una persona por número de documento
        GET /api/v1/extension/persona/{numero_documento}
        """
        persona = ExtensionService.get_persona_por_dni(numero_documento)
        if not persona:
            return Response(
                {'detail': f'No se encontró persona con DNI {numero_documento}'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(persona, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['put'], url_path='solicitud/(?P<numero_documento>[^/.]+)/estado')
    def actualizar_estado_solicitud(self, request, numero_documento=None):
        """
        Actualizar estado de una solicitud HPS
        PUT /api/v1/extension/solicitud/{numero_documento}/estado
        Body: {"estado": "submitted"}
        """
        nuevo_estado = request.data.get('estado')
        if not nuevo_estado:
            return Response(
                {'detail': 'El campo "estado" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = ExtensionService.actualizar_estado_solicitud(numero_documento, nuevo_estado)
        
        if not result['success']:
            return Response(
                {'detail': result['message']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(result, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['put'], url_path='solicitud/(?P<numero_documento>[^/.]+)/enviada')
    def marcar_solicitud_enviada(self, request, numero_documento=None):
        """
        Marcar solicitud como enviada (cambiar estado a 'submitted')
        PUT /api/v1/extension/solicitud/{numero_documento}/enviada
        """
        result = ExtensionService.actualizar_estado_solicitud(numero_documento, 'submitted')
        
        if not result['success']:
            return Response(
                {'detail': result['message']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(result, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['put'], url_path='traslado/(?P<numero_documento>[^/.]+)/enviado')
    def marcar_traslado_enviado(self, request, numero_documento=None):
        """
        Marcar traslado como enviado (cambiar estado a 'submitted')
        PUT /api/v1/extension/traslado/{numero_documento}/enviado
        """
        result = ExtensionService.actualizar_estado_solicitud(numero_documento, 'submitted')
        
        if not result['success']:
            return Response(
                {'detail': result['message']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(result, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='traslado/(?P<numero_documento>[^/.]+)/pdf')
    def descargar_pdf_traslado(self, request, numero_documento=None):
        """
        Descargar PDF de traslado por número de documento
        GET /api/v1/extension/traslado/{numero_documento}/pdf
        """
        try:
            hps_request = models.HpsRequest.objects.filter(
                document_number=numero_documento,
                form_type='traslado',
                status='pending'
            ).first()
            
            if not hps_request:
                return Response(
                    {'detail': 'Traslado no encontrado o no está pendiente'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if not hps_request.filled_pdf:
                return Response(
                    {'detail': 'No hay PDF rellenado para este traslado'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Generar nombre del archivo
            user_name = f"{hps_request.first_name} {hps_request.first_last_name}".strip()
            if hps_request.second_last_name:
                user_name += f" {hps_request.second_last_name}"
            
            # Limpiar caracteres no válidos
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', user_name)
            filename = f"{safe_name} - Traslado HPS.pdf"
            
            return FileResponse(
                hps_request.filled_pdf.open('rb'),
                content_type='application/pdf',
                filename=filename,
                as_attachment=True
            )
            
        except Exception as e:
            logger.error(f"Error descargando PDF de traslado: {e}")
            return Response(
                {'detail': f'Error descargando PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChatConversationViewSet(viewsets.ModelViewSet):
    """ViewSet para conversaciones de chat"""
    queryset = models.ChatConversation.objects.select_related('user')
    serializer_class = serializers.ChatConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar conversaciones por usuario autenticado"""
        qs = super().get_queryset()
        return qs.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Asignar usuario automáticamente al crear conversación"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request):
        """Obtener conversación activa del usuario"""
        user_id = request.query_params.get('user_id')
        if user_id and str(request.user.id) != str(user_id):
            return Response(
                {'detail': 'No tienes permiso para ver esta conversación'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        conversation = models.ChatConversation.objects.filter(
            user=request.user,
            status='active'
        ).order_by('-created_at').first()
        
        if conversation:
            serializer = self.get_serializer(conversation)
            return Response({'conversation_id': str(conversation.id), **serializer.data})
        return Response({'conversation_id': None})
    
    @action(detail=False, methods=['post'], url_path='archive-active')
    def archive_active(self, request):
        """Archivar conversación activa del usuario actual"""
        try:
            conversation = models.ChatConversation.objects.filter(
                user=request.user,
                status='active'
            ).order_by('-created_at').first()
            
            if not conversation:
                return Response({
                    'success': True,
                    'message': 'No hay conversación activa para archivar',
                    'archived_conversation_id': None
                }, status=status.HTTP_200_OK)
            
            conversation.status = 'archived'
            conversation.closed_at = datetime.now()
            conversation.save()
            
            logger.info(f"Conversación {conversation.id} archivada para usuario {request.user.id}")
            
            return Response({
                'success': True,
                'message': 'Conversación archivada exitosamente',
                'archived_conversation_id': str(conversation.id)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error archivando conversación: {e}")
            return Response(
                {'detail': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """Completar una conversación"""
        conversation = self.get_object()
        if conversation.user != request.user:
            return Response(
                {'detail': 'No tienes permiso para completar esta conversación'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        conversation.status = 'closed'
        conversation.completed_at = datetime.now()
        conversation.save()
        
        serializer = self.get_serializer(conversation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='abandon')
    def abandon(self, request, pk=None):
        """Abandonar una conversación"""
        conversation = self.get_object()
        if conversation.user != request.user:
            return Response(
                {'detail': 'No tienes permiso para abandonar esta conversación'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        conversation.status = 'closed'
        conversation.closed_at = datetime.now()
        conversation.save()
        
        serializer = self.get_serializer(conversation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='messages')
    def messages(self, request, pk=None):
        """Obtener mensajes de una conversación"""
        conversation = self.get_object()
        if conversation.user != request.user:
            return Response(
                {'detail': 'No tienes permiso para ver estos mensajes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        messages = conversation.messages.all().order_by('created_at')
        message_serializer = serializers.ChatMessageSerializer(messages, many=True)
        return Response({'messages': message_serializer.data})
    
    @action(detail=True, methods=['get'], url_path='full')
    def full(self, request, pk=None):
        """Obtener conversación completa con todos los mensajes"""
        conversation = self.get_object()
        if conversation.user != request.user and not request.user.is_staff:
            return Response(
                {'detail': 'No tienes permiso para ver esta conversación'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        messages = conversation.messages.all().order_by('created_at')
        message_serializer = serializers.ChatMessageSerializer(messages, many=True)
        conversation_serializer = self.get_serializer(conversation)
        
        return Response({
            'conversation': conversation_serializer.data,
            'messages': message_serializer.data
        })
    
    @action(detail=False, methods=['post'], url_path='reset')
    def reset(self, request):
        """
        Resetear conversación: cerrar la conversación activa actual y crear una nueva.
        Compatible con el frontend de hps-system.
        
        POST /api/hps/chat/conversations/reset/
        """
        try:
            from django.utils import timezone
            import uuid
            
            # Cerrar todas las conversaciones activas del usuario
            active_conversations = models.ChatConversation.objects.filter(
                user=request.user,
                status='active'
            )
            
            closed_count = active_conversations.update(
                status='closed',
                closed_at=timezone.now()
            )
            
            # Crear una nueva conversación activa
            new_session_id = str(uuid.uuid4())
            new_conversation = models.ChatConversation.objects.create(
                user=request.user,
                session_id=new_session_id,
                title='Nueva conversación',
                status='active',
                total_messages=0,
                total_tokens_used=0
            )
            
            serializer = self.get_serializer(new_conversation)
            return Response({
                'success': True,
                'message': f'Conversación reseteada. {closed_count} conversación(es) cerrada(s).',
                'conversation_id': str(new_conversation.id),
                'session_id': new_session_id,
                **serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error reseteando conversación: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'detail': f'Error reseteando conversación: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChatMessageViewSet(viewsets.ModelViewSet):
    """ViewSet para mensajes de chat"""
    queryset = models.ChatMessage.objects.select_related('conversation')
    serializer_class = serializers.ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar mensajes por conversaciones del usuario"""
        qs = super().get_queryset()
        return qs.filter(conversation__user=self.request.user)
    
    def perform_create(self, serializer):
        """Validar que la conversación pertenece al usuario"""
        conversation_id = serializer.validated_data.get('conversation')
        if conversation_id and conversation_id.user != self.request.user:
            raise serializers.ValidationError(
                'No tienes permiso para crear mensajes en esta conversación'
            )
        serializer.save()


# Endpoints adicionales para integración con agente IA
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_hps_by_email(request, email):
    """Aprobar HPS pendiente por email del usuario"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = User.objects.filter(email=email).first()
        if not user:
            return Response(
                {'detail': f'Usuario con email {email} no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Buscar HPS pendiente del usuario
        hps_request = models.HpsRequest.objects.filter(
            user=user,
            status='pending'
        ).order_by('-created_at').first()
        
        if not hps_request:
            return Response(
                {'detail': f'No hay HPS pendiente para el usuario {email}'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Aprobar usando el método del ViewSet
        viewset = HpsRequestViewSet()
        viewset.request = request
        viewset.format_kwarg = None
        viewset.kwargs = {'pk': str(hps_request.id)}
        
        return viewset.approve(request, pk=str(hps_request.id))
        
    except Exception as e:
        logger.error(f"Error aprobando HPS por email: {e}")
        return Response(
            {'detail': f'Error aprobando HPS: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_users(request):
    """Buscar usuarios por query (email, nombre, etc.)"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        query = request.query_params.get('q', '')
        limit = int(request.query_params.get('limit', 10))
        
        if not query:
            return Response({'users': []})
        
        # Buscar por email o nombre
        users = User.objects.filter(
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query)
        )[:limit]
        
        user_list = []
        for user in users:
            profile = getattr(user, 'hps_profile', None)
            user_list.append({
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'role': profile.role.name if profile and profile.role else None,
                'team_id': profile.team.id if profile and profile.team else None,
            })
        
        return Response({'users': user_list})
        
    except Exception as e:
        logger.error(f"Error buscando usuarios: {e}")
        return Response(
            {'detail': f'Error buscando usuarios: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_user_exists(request, email):
    """Verificar si existe un usuario con el email dado"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        exists = User.objects.filter(email=email).exists()
        return Response({'exists': exists}, status=status.HTTP_200_OK if exists else status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Error verificando usuario: {e}")
        return Response(
            {'detail': f'Error verificando usuario: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_email_async(request):
    """
    Endpoint para envío asíncrono de emails genéricos.
    Compatible con el frontend de hps-system.
    
    POST /api/hps/email/send/
    Body: {
        "to": "email@example.com",
        "subject": "Asunto del email",
        "body": "Cuerpo del email (texto plano)",
        "html_body": "<html>Cuerpo HTML</html>",  # Opcional
        "from_email": "remitente@example.com",  # Opcional, usa DEFAULT_FROM_EMAIL si no se proporciona
        "reply_to": "reply@example.com"  # Opcional
    }
    """
    try:
        from .tasks import send_generic_email_task
        
        email_data = {
            "to": request.data.get("to"),
            "subject": request.data.get("subject"),
            "body": request.data.get("body"),
            "html_body": request.data.get("html_body"),
            "from_email": request.data.get("from_email"),
            "reply_to": request.data.get("reply_to")
        }
        
        # Validar campos requeridos
        if not email_data["to"]:
            return Response(
                {"error": "El campo 'to' es requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not email_data["subject"]:
            return Response(
                {"error": "El campo 'subject' es requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not email_data["body"]:
            return Response(
                {"error": "El campo 'body' es requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Enviar tarea a Celery
        task = send_generic_email_task.delay(email_data)
        
        return Response({
            "success": True,
            "task_id": task.id,
            "status": "queued",
            "message": "Email encolado para envío"
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        logger.error(f"Error encolando email: {str(e)}")
        return Response({
            "error": f"Error encolando email: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_bulk_emails_async(request):
    """
    Endpoint para envío masivo asíncrono de emails.
    Compatible con el frontend de hps-system.
    
    POST /api/hps/email/send-bulk/
    Body: {
        "emails": [
            {
                "to": "email1@example.com",
                "subject": "Asunto 1",
                "body": "Cuerpo 1",
                "html_body": "<html>Cuerpo HTML 1</html>"  # Opcional
            },
            {
                "to": "email2@example.com",
                "subject": "Asunto 2",
                "body": "Cuerpo 2"
            }
        ]
    }
    """
    try:
        from .tasks import send_bulk_emails_task
        
        emails_data = request.data.get("emails", [])
        
        if not emails_data or not isinstance(emails_data, list):
            return Response(
                {"error": "El campo 'emails' debe ser una lista no vacía"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar cada email
        for email_data in emails_data:
            if not email_data.get("to"):
                return Response(
                    {"error": f"El campo 'to' es requerido para todos los emails"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not email_data.get("subject"):
                return Response(
                    {"error": f"El campo 'subject' es requerido para todos los emails"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not email_data.get("body"):
                return Response(
                    {"error": f"El campo 'body' es requerido para todos los emails"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Enviar tarea a Celery
        task = send_bulk_emails_task.delay(emails_data)
        
        return Response({
            "success": True,
            "task_id": task.id,
            "status": "queued",
            "total_emails": len(emails_data),
            "message": f"{len(emails_data)} emails encolados para envío"
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        logger.error(f"Error encolando emails masivos: {str(e)}")
        return Response({
            "error": f"Error encolando emails masivos: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_task_status(request, task_id):
    """
    Obtener estado de una tarea Celery.
    Compatible con el frontend de hps-system.
    
    GET /api/hps/email/task/<task_id>/
    """
    try:
        from celery.result import AsyncResult
        
        task_result = AsyncResult(task_id)
        
        response_data = {
            "task_id": task_id,
            "status": task_result.status,
            "ready": task_result.ready(),
        }
        
        if task_result.ready():
            if task_result.successful():
                response_data["result"] = task_result.result
                response_data["success"] = True
            else:
                response_data["error"] = str(task_result.info)
                response_data["success"] = False
        else:
            # Tarea aún en progreso
            if task_result.state == "PROGRESS":
                response_data["progress"] = task_result.info.get("progress", 0)
                response_data["current_status"] = task_result.info.get("status", "Procesando...")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de tarea {task_id}: {str(e)}")
        return Response({
            "error": f"Error obteniendo estado de tarea: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_hps_form_email_async(request):
    """Enviar email con formulario HPS de forma asíncrona"""
    try:
        from hps_core.tasks import send_hps_form_email_task
        
        # Aceptar parámetros tanto de query string como del body JSON
        email = request.query_params.get('email') or request.data.get('email')
        form_url = request.query_params.get('form_url') or request.data.get('form_url')
        user_name = request.query_params.get('user_name') or request.data.get('user_name', '')
        
        if not email or not form_url:
            return Response(
                {'detail': 'Email y form_url son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # No requerir que el usuario exista - puede ser un nuevo usuario que se creará al completar el formulario
        # Si no hay user_name, generar uno a partir del email
        if not user_name:
            user_name = email.split("@")[0].replace(".", " ").title()
        
        # Enviar email de forma asíncrona usando Celery
        task = send_hps_form_email_task.delay(email, form_url, user_name)
        
        return Response({
            'status': 'success',
            'message': 'Email encolado para envío asíncrono',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        logger.error(f"Error enviando email HPS: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return Response(
            {'detail': f'Error enviando email: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# Endpoints de monitoreo de chat
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_realtime_metrics(request):
    """
    Obtener métricas en tiempo real del chat.
    Compatible con el frontend de hps-system.
    
    GET /api/hps/chat/metrics/realtime/
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Usuarios activos en las últimas 24 horas
        active_users_24h = models.ChatConversation.objects.filter(
            created_at__gte=last_24h
        ).values('user').distinct().count()
        
        # Mensajes hoy
        total_messages_today = models.ChatMessage.objects.filter(
            created_at__gte=today_start
        ).count()
        
        # Conversaciones activas
        active_conversations = models.ChatConversation.objects.filter(
            status='active'
        ).count()
        
        # Tasa de error (mensajes con error)
        total_messages_24h = models.ChatMessage.objects.filter(
            created_at__gte=last_24h
        ).count()
        error_messages_24h = models.ChatMessage.objects.filter(
            created_at__gte=last_24h,
            is_error=True
        ).count()
        error_rate = (error_messages_24h / total_messages_24h * 100) if total_messages_24h > 0 else 0
        
        # Tiempo promedio de respuesta
        from django.db.models import Avg
        avg_response_time_result = models.ChatMessage.objects.filter(
            created_at__gte=last_24h,
            message_type='assistant',
            response_time_ms__isnull=False
        ).aggregate(avg=Avg('response_time_ms'))
        avg_response_time_ms = avg_response_time_result['avg'] or 0
        
        # Score de salud del sistema (0-100)
        system_health_score = 100.0
        if error_rate > 10:
            system_health_score -= 30
        elif error_rate > 5:
            system_health_score -= 15
        if avg_response_time_ms > 5000:
            system_health_score -= 20
        elif avg_response_time_ms > 3000:
            system_health_score -= 10
        
        return Response({
            'active_users_24h': active_users_24h,
            'total_messages_today': total_messages_today,
            'active_conversations': active_conversations,
            'error_rate': round(error_rate, 2),
            'avg_response_time_ms': round(avg_response_time_ms, 2),
            'system_health_score': max(0, min(100, round(system_health_score, 2)))
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error obteniendo métricas en tiempo real: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return Response(
            {'detail': f'Error obteniendo métricas: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_historical_metrics(request):
    """
    Obtener métricas históricas del chat.
    Compatible con el frontend de hps-system.
    
    GET /api/hps/chat/metrics/historical/?days=7
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Avg, Count
        
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        # Agrupar por día
        metrics_by_day = []
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            conversations = models.ChatConversation.objects.filter(
                created_at__gte=day_start,
                created_at__lt=day_end
            )
            messages = models.ChatMessage.objects.filter(
                created_at__gte=day_start,
                created_at__lt=day_end
            )
            
            metrics_by_day.append({
                'date': day_start.date().isoformat(),
                'conversations': conversations.count(),
                'messages': messages.count(),
                'tokens_used': sum(c.total_tokens_used for c in conversations),
                'active_users': conversations.values('user').distinct().count()
            })
        
        return Response({
            'historical_metrics': metrics_by_day
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error obteniendo métricas históricas: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return Response(
            {'detail': f'Error obteniendo métricas históricas: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_analytics(request):
    """
    Obtener análisis completo del chat.
    Compatible con el frontend de hps-system.
    
    GET /api/hps/chat/analytics/?days=7
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Avg, Count
        
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        last_24h = timezone.now() - timedelta(hours=24)
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Calcular métricas en tiempo real directamente
        active_users_24h = models.ChatConversation.objects.filter(
            created_at__gte=last_24h
        ).values('user').distinct().count()
        
        total_messages_today = models.ChatMessage.objects.filter(
            created_at__gte=today_start
        ).count()
        
        active_conversations = models.ChatConversation.objects.filter(
            status='active'
        ).count()
        
        total_messages_24h = models.ChatMessage.objects.filter(
            created_at__gte=last_24h
        ).count()
        error_messages_24h = models.ChatMessage.objects.filter(
            created_at__gte=last_24h,
            is_error=True
        ).count()
        error_rate = (error_messages_24h / total_messages_24h * 100) if total_messages_24h > 0 else 0
        
        avg_response_time_result = models.ChatMessage.objects.filter(
            created_at__gte=last_24h,
            message_type='assistant',
            response_time_ms__isnull=False
        ).aggregate(avg=Avg('response_time_ms'))
        avg_response_time_ms = avg_response_time_result['avg'] or 0
        
        system_health_score = 100.0
        if error_rate > 10:
            system_health_score -= 30
        elif error_rate > 5:
            system_health_score -= 15
        if avg_response_time_ms > 5000:
            system_health_score -= 20
        elif avg_response_time_ms > 3000:
            system_health_score -= 10
        
        realtime_metrics = {
            'active_users_24h': active_users_24h,
            'total_messages_today': total_messages_today,
            'active_conversations': active_conversations,
            'error_rate': round(error_rate, 2),
            'avg_response_time_ms': round(avg_response_time_ms, 2),
            'system_health_score': max(0, min(100, round(system_health_score, 2)))
        }
        
        # Calcular métricas históricas directamente
        metrics_by_day = []
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            conversations = models.ChatConversation.objects.filter(
                created_at__gte=day_start,
                created_at__lt=day_end
            )
            messages = models.ChatMessage.objects.filter(
                created_at__gte=day_start,
                created_at__lt=day_end
            )
            
            metrics_by_day.append({
                'date': day_start.date().isoformat(),
                'conversations': conversations.count(),
                'messages': messages.count(),
                'tokens_used': sum(c.total_tokens_used for c in conversations),
                'active_users': conversations.values('user').distinct().count()
            })
        
        historical_metrics = metrics_by_day
        
        # Conversaciones recientes
        recent_conversations = models.ChatConversation.objects.filter(
            created_at__gte=start_date
        ).select_related('user').order_by('-created_at')[:20]
        
        conversation_serializer = serializers.ChatConversationSerializer(recent_conversations, many=True)
        
        # Temas más frecuentes (simplificado - basado en palabras clave en mensajes)
        # TODO: Implementar análisis más sofisticado de temas
        top_topics = []
        
        # Rendimiento del agente
        agent_performance = {
            'avg_response_time_ms': realtime_metrics.get('avg_response_time_ms', 0),
            'error_rate': realtime_metrics.get('error_rate', 0),
            'total_responses': models.ChatMessage.objects.filter(
                created_at__gte=start_date,
                message_type='assistant'
            ).count()
        }
        
        return Response({
            'realtime_metrics': realtime_metrics,
            'historical_metrics': historical_metrics,
            'recent_conversations': conversation_serializer.data,
            'top_topics': top_topics,
            'agent_performance': agent_performance
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error obteniendo análisis del chat: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return Response(
            {'detail': f'Error obteniendo análisis: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_performance(request):
    """
    Obtener rendimiento del agente IA.
    Compatible con el frontend de hps-system.
    
    GET /api/hps/chat/performance/
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        last_24h = timezone.now() - timedelta(hours=24)
        
        # Calcular métricas de rendimiento
        total_responses = models.ChatMessage.objects.filter(
            created_at__gte=last_24h,
            message_type='assistant'
        ).count()
        
        error_responses = models.ChatMessage.objects.filter(
            created_at__gte=last_24h,
            message_type='assistant',
            is_error=True
        ).count()
        
        response_times = models.ChatMessage.objects.filter(
            created_at__gte=last_24h,
            message_type='assistant',
            response_time_ms__isnull=False
        ).values_list('response_time_ms', flat=True)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return Response({
            'total_responses_24h': total_responses,
            'error_responses_24h': error_responses,
            'success_rate': ((total_responses - error_responses) / total_responses * 100) if total_responses > 0 else 0,
            'avg_response_time_ms': round(avg_response_time, 2)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error obteniendo rendimiento del agente: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return Response(
            {'detail': f'Error obteniendo rendimiento: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_topics(request):
    """
    Obtener temas más frecuentes.
    Compatible con el frontend de hps-system.
    
    GET /api/hps/chat/topics/?limit=10
    """
    try:
        limit = int(request.query_params.get('limit', 10))
        
        # TODO: Implementar análisis de temas más sofisticado
        # Por ahora, devolver lista vacía
        top_topics = []
        
        return Response({
            'topics': top_topics
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error obteniendo temas: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return Response(
            {'detail': f'Error obteniendo temas: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

