from django.urls import path
from rest_framework import routers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import logging

from . import views
from .extension_service import ExtensionService
from .models import HpsRequest
from django.http import FileResponse
import re

logger = logging.getLogger(__name__)


router = routers.DefaultRouter()
router.register(r"hps/roles", views.HpsRoleViewSet, basename="hps-role")
router.register(r"hps/teams", views.HpsTeamViewSet, basename="hps-team")
router.register(r"hps/requests", views.HpsRequestViewSet, basename="hps-request")
router.register(r"hps/tokens", views.HpsTokenViewSet, basename="hps-token")
router.register(r"hps/audit-logs", views.HpsAuditLogViewSet, basename="hps-audit-log")
router.register(r"hps/user/profiles", views.HpsUserProfileViewSet, basename="hps-user-profile")
router.register(r"extension", views.HpsExtensionViewSet, basename="hps-extension")
# Endpoints de chat
router.register(r"hps/chat/conversations", views.ChatConversationViewSet, basename="chat-conversation")
router.register(r"hps/chat/messages", views.ChatMessageViewSet, basename="chat-message")


# Endpoints de extensiones con parámetros en la URL (públicos, sin autenticación)
@api_view(['GET'])
@permission_classes([AllowAny])
def extension_personas_pendientes(request):
    """GET /api/v1/extension/personas?tipo=solicitud"""
    tipo = request.query_params.get('tipo')
    personas = ExtensionService.get_personas_pendientes(tipo)
    return Response(personas, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def extension_persona_por_dni(request, numero_documento):
    """GET /api/v1/extension/persona/{numero_documento}"""
    persona = ExtensionService.get_persona_por_dni(numero_documento)
    if not persona:
        return Response(
            {'detail': f'No se encontró persona con DNI {numero_documento}'},
            status=status.HTTP_404_NOT_FOUND
        )
    return Response(persona, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([AllowAny])
def extension_actualizar_estado(request, numero_documento):
    """PUT /api/v1/extension/solicitud/{numero_documento}/estado"""
    nuevo_estado = request.data.get('estado')
    if not nuevo_estado:
        return Response(
            {'detail': 'El campo "estado" es requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    result = ExtensionService.actualizar_estado_solicitud(numero_documento, nuevo_estado)
    if not result['success']:
        return Response({'detail': result['message']}, status=status.HTTP_400_BAD_REQUEST)
    return Response(result, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([AllowAny])
def extension_marcar_enviada(request, numero_documento):
    """PUT /api/v1/extension/solicitud/{numero_documento}/enviada"""
    result = ExtensionService.actualizar_estado_solicitud(numero_documento, 'submitted')
    if not result['success']:
        return Response({'detail': result['message']}, status=status.HTTP_400_BAD_REQUEST)
    return Response(result, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([AllowAny])
def extension_marcar_traslado_enviado(request, numero_documento):
    """PUT /api/v1/extension/traslado/{numero_documento}/enviado"""
    result = ExtensionService.actualizar_estado_solicitud(numero_documento, 'submitted')
    if not result['success']:
        return Response({'detail': result['message']}, status=status.HTTP_400_BAD_REQUEST)
    return Response(result, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def extension_descargar_pdf_traslado(request, numero_documento):
    """GET /api/v1/extension/traslado/{numero_documento}/pdf"""
    try:
        hps_request = HpsRequest.objects.filter(
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
        
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', user_name)
        filename = f"{safe_name} - Traslado HPS.pdf"
        
        return FileResponse(
            hps_request.filled_pdf.open('rb'),
            content_type='application/pdf',
            filename=filename,
            as_attachment=True
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error descargando PDF de traslado: {e}")
        return Response(
            {'detail': f'Error descargando PDF: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hps_user_profile(request):
    """
    Obtener información del perfil HPS del usuario actual
    Compatible con el frontend de hps-system
    """
    try:
        user = request.user
        
        # Si no tiene perfil HPS, devolver información básica
        if not hasattr(user, 'hps_profile') or not user.hps_profile:
            return Response({
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': f"{user.first_name} {user.last_name}".strip(),
                'role': None,
                'is_active': user.is_active,
                'is_temp_password': False,
                'must_change_password': False,
                'team_id': None,
                'team_name': None,
            }, status=status.HTTP_200_OK)
        
        profile = user.hps_profile
        
        return Response({
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': f"{user.first_name} {user.last_name}".strip(),
            'role': profile.role.name if profile.role else None,
            'is_active': user.is_active,
            'is_temp_password': profile.is_temp_password,
            'must_change_password': profile.must_change_password,
            'team_id': profile.team.id if profile.team else None,
            'team_name': profile.team.name if profile.team else None,
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error obteniendo perfil HPS: {str(e)}")
        return Response({
            'error': f'Error al obtener perfil HPS: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


urlpatterns = router.urls + [
    # Endpoint de perfil HPS
    path('hps/user/profile/', hps_user_profile, name='hps-user-profile'),
    
    # Endpoints de email (asíncronos con Celery)
    path('hps/email/send/', views.send_email_async, name='hps-email-send'),
    path('hps/email/send-bulk/', views.send_bulk_emails_async, name='hps-email-send-bulk'),
    path('hps/email/task/<str:task_id>/', views.get_task_status, name='hps-email-task-status'),
    
    # Endpoints de extensiones (públicos para el complemento de navegador)
    path('extension/personas/', extension_personas_pendientes, name='extension-personas'),
    path('extension/persona/<str:numero_documento>/', extension_persona_por_dni, name='extension-persona-dni'),
    path('extension/solicitud/<str:numero_documento>/estado/', extension_actualizar_estado, name='extension-solicitud-estado'),
    path('extension/solicitud/<str:numero_documento>/enviada/', extension_marcar_enviada, name='extension-solicitud-enviada'),
    path('extension/traslado/<str:numero_documento>/enviado/', extension_marcar_traslado_enviado, name='extension-traslado-enviado'),
    path('extension/traslado/<str:numero_documento>/pdf/', extension_descargar_pdf_traslado, name='extension-traslado-pdf'),
    
    # Endpoints adicionales para integración con agente IA
    path('hps/approve/<str:email>/', views.approve_hps_by_email, name='hps-approve-by-email'),
    path('users/search/query/', views.search_users, name='users-search'),
    path('users/check/<str:email>/', views.check_user_exists, name='users-check'),
    path('email/send-hps-form-async/', views.send_hps_form_email_async, name='email-send-hps-form'),
]

