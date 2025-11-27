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
from .permissions import HasHpsProfile, IsHpsAdmin, IsHpsAdminOrSelf, IsHpsAdminOrTeamLead
from .services import HpsRequestService
from .extension_service import ExtensionService
from django.http import FileResponse, Http404
import re


ADMIN_ROLES = {"admin", "jefe_seguridad", "security_chief"}
TEAM_ROLES = {"team_lead", "team_leader", "jefe_seguridad_suplente"}


class HpsRoleViewSet(viewsets.ModelViewSet):
    queryset = models.HpsRole.objects.all()
    serializer_class = serializers.HpsRoleSerializer
    permission_classes = [permissions.IsAuthenticated, IsHpsAdmin]


class HpsTeamViewSet(viewsets.ModelViewSet):
    queryset = models.HpsTeam.objects.prefetch_related("memberships")
    serializer_class = serializers.HpsTeamSerializer
    permission_classes = [permissions.IsAuthenticated, IsHpsAdminOrTeamLead]


class HpsRequestViewSet(viewsets.ModelViewSet):
    queryset = models.HpsRequest.objects.select_related(
        "user", "submitted_by", "approved_by", "template"
    )
    serializer_class = serializers.HpsRequestSerializer
    permission_classes = [permissions.IsAuthenticated, HasHpsProfile]

    def _profile(self):
        user = self.request.user
        return getattr(user, "hps_profile", None)

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get("status")
        request_type = self.request.query_params.get("request_type")
        form_type = self.request.query_params.get("form_type")
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

        if role_name in TEAM_ROLES and profile.team_id:
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
            waiting_dps_requests=Count("id", filter=Q(status="waiting_dps")),  # Estado que no existe en el modelo, siempre será 0
            submitted_requests=Count("id", filter=Q(status=models.HpsRequest.RequestStatus.SUBMITTED)),
            approved_requests=Count("id", filter=Q(status=models.HpsRequest.RequestStatus.APPROVED)),
            rejected_requests=Count("id", filter=Q(status=models.HpsRequest.RequestStatus.REJECTED)),
            expired_requests=Count("id", filter=Q(status=models.HpsRequest.RequestStatus.EXPIRED)),
        )
        # Asegurar que waiting_dps_requests sea 0 si no existe
        if data.get("waiting_dps_requests") is None:
            data["waiting_dps_requests"] = 0
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

        hps_request.status = models.HpsRequest.RequestStatus.SUBMITTED
        hps_request.submitted_at = datetime.now()
        hps_request.submitted_by = request.user
        if notes:
            # Guardar notas en algún campo si existe, o crear un audit log
            pass
        hps_request.save()

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
        form_type = request.query_params.get("form_type") or request.query_params.get("hps_type", "solicitud")
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
    permission_classes = [permissions.IsAuthenticated, IsHpsAdmin]
    
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
    
    @action(detail=False, methods=['get'], url_path='validate', permission_classes=[permissions.AllowAny])
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


class HpsAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.HpsAuditLog.objects.select_related("user")
    serializer_class = serializers.HpsAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsHpsAdminOrSelf]


class HpsUserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para listar y ver perfiles de usuario HPS
    Todos los usuarios con perfil HPS pueden acceder, con filtros según su rol
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
        if role_name in TEAM_ROLES and profile.team_id:
            return qs.filter(team_id=profile.team_id)
        
        # Otros usuarios (members) pueden ver todos los usuarios también
        # Según el requerimiento: todos los usuarios deben aparecer en la gestión
        return qs
    


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

