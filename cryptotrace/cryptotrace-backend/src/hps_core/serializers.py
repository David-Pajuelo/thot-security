from django.contrib.auth import get_user_model
from rest_framework import serializers

from . import models


User = get_user_model()


class HpsRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HpsRole
        fields = [
            "id",
            "name",
            "description",
            "permissions",
            "created_at",
            "updated_at",
        ]


class HpsTeamSerializer(serializers.ModelSerializer):
    team_lead = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), allow_null=True, required=False
    )
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = models.HpsTeam
        fields = [
            "id",
            "name",
            "description",
            "team_lead",
            "is_active",
            "member_count",
            "created_at",
            "updated_at",
        ]


class HpsRequestSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    submitted_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    approved_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), allow_null=True, required=False
    )
    # Campos calculados
    is_expired = serializers.BooleanField(read_only=True)
    can_be_approved = serializers.SerializerMethodField()
    # Información de usuarios relacionados (opcional)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    submitted_by_email = serializers.CharField(source='submitted_by.email', read_only=True)
    approved_by_email = serializers.CharField(source='approved_by.email', read_only=True, allow_null=True)

    class Meta:
        model = models.HpsRequest
        fields = "__all__"
        read_only_fields = [
            "created_at",
            "updated_at",
            "submitted_at",
            "approved_at",
            "auto_processed_at",
            "is_expired",
        ]
        extra_kwargs = {
            "user": {"required": False},
            "submitted_by": {"required": False},
        }
    
    def get_can_be_approved(self, obj):
        """Verifica si la solicitud puede ser aprobada"""
        return obj.status == 'pending' and not obj.is_expired
    
    def get_user_full_name(self, obj):
        """Obtiene el nombre completo del usuario"""
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return ""


class HpsTokenSerializer(serializers.ModelSerializer):
    requested_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False  # Se asignará automáticamente en perform_create
    )
    token = serializers.CharField(read_only=True)  # Se genera automáticamente
    expires_at = serializers.DateTimeField(read_only=True)  # Se genera automáticamente
    hours_valid = serializers.IntegerField(write_only=True, required=False, default=72)  # Para controlar validez

    class Meta:
        model = models.HpsToken
        fields = "__all__"
        read_only_fields = ["token", "expires_at", "is_used", "used_at", "created_at", "updated_at"]


class HpsAuditLogSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = models.HpsAuditLog
        fields = "__all__"
        read_only_fields = ["created_at"]


class HpsUserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para perfiles de usuario HPS
    Incluye información del usuario, rol y equipo relacionados
    """
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    full_name = serializers.SerializerMethodField()
    role = serializers.CharField(source='role.name', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    team_id = serializers.SerializerMethodField()
    team_name = serializers.CharField(source='team.name', read_only=True, allow_null=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    created_at = serializers.DateTimeField(source='user.date_joined', read_only=True)
    updated_at = serializers.DateTimeField(source='user.date_joined', read_only=True)

    class Meta:
        model = models.HpsUserProfile
        fields = [
            "id",
            "user_id",
            "email",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "role_name",
            "team_id",
            "team_name",
            "is_active",
            "is_temp_password",
            "must_change_password",
            "email_verified",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
    
    def get_full_name(self, obj):
        """Obtiene el nombre completo del usuario"""
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return ""
    
    def get_team_id(self, obj):
        """Obtiene el team_id como string UUID si existe"""
        if obj.team:
            return str(obj.team.id)
        return None


class ChatConversationSerializer(serializers.ModelSerializer):
    """Serializer para conversaciones de chat"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)  # Para compatibilidad con agente IA
    
    class Meta:
        model = models.ChatConversation
        fields = [
            "id",
            "user",
            "user_id",
            "user_email",
            "session_id",
            "title",
            "status",
            "total_messages",
            "total_tokens_used",
            "conversation_data",
            "created_at",
            "updated_at",
            "completed_at",
            "closed_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at", "completed_at", "closed_at"]


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer para mensajes de chat"""
    conversation_id = serializers.UUIDField(write_only=True, required=False)  # Para compatibilidad con agente IA
    
    class Meta:
        model = models.ChatMessage
        fields = [
            "id",
            "conversation",
            "conversation_id",
            "message_type",
            "content",
            "tokens_used",
            "response_time_ms",
            "is_error",
            "error_message",
            "message_metadata",
            "created_at",
        ]
        read_only_fields = ["created_at"]
    
    def validate(self, attrs):
        """Validar y convertir conversation_id a conversation si es necesario"""
        conversation_id = attrs.pop('conversation_id', None)
        if conversation_id and not attrs.get('conversation'):
            try:
                conversation = models.ChatConversation.objects.get(id=conversation_id)
                attrs['conversation'] = conversation
            except models.ChatConversation.DoesNotExist:
                raise serializers.ValidationError(f'Conversación {conversation_id} no encontrada')
        
        # Convertir message_metadata de dict a JSON string si es necesario
        if 'message_metadata' in attrs and isinstance(attrs['message_metadata'], dict):
            import json
            attrs['message_metadata'] = json.dumps(attrs['message_metadata'])
        
        return attrs

