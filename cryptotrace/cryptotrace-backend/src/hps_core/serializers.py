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
        allow_null=True, required=False, read_only=True
    )
    team_lead_id = serializers.SerializerMethodField(read_only=True)
    team_lead_id_writable = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    team_lead_name = serializers.SerializerMethodField()
    member_count = serializers.IntegerField(read_only=True)
    members = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.HpsTeam
        fields = [
            "id",
            "name",
            "description",
            "team_lead",
            "team_lead_id",
            "team_lead_id_writable",
            "team_lead_name",
            "is_active",
            "member_count",
            "members",
            "created_at",
            "updated_at",
        ]
    
    def get_team_lead_id(self, obj):
        """Obtener el ID del líder del equipo como entero"""
        if obj.team_lead:
            return obj.team_lead.id
        return None
    
    def get_team_lead_name(self, obj):
        """Obtener el nombre completo del líder del equipo"""
        if obj.team_lead:
            full_name = f"{obj.team_lead.first_name} {obj.team_lead.last_name}".strip()
            return full_name if full_name else obj.team_lead.email
        return None
    
    def get_members(self, obj):
        """Obtener lista de miembros del equipo"""
        members = models.HpsUserProfile.objects.filter(
            team=obj,
            user__is_active=True
        ).select_related('user', 'role')
        
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
        
        return members_list
    
    def create(self, validated_data):
        """
        Crear equipo, manejando team_lead_id_writable y actualizando roles de usuarios.
        
        Lógica de asignación de líder:
        - Si el usuario tiene rol "member" y se le asigna como líder, cambiar a "team_lead"
        - Si el usuario tiene otro rol (crypto, admin, etc.), mantenerlo pero internamente tiene permisos de líder
        """
        import logging
        logger = logging.getLogger(__name__)
        
        team_lead_id_writable = validated_data.pop('team_lead_id_writable', None)
        # También aceptar team_lead_id para compatibilidad
        team_lead_id = validated_data.pop('team_lead_id', None)
        
        # Usar team_lead_id_writable si está presente, sino team_lead_id
        lead_id = team_lead_id_writable if team_lead_id_writable is not None else team_lead_id
        
        if lead_id is not None and lead_id != '':
            try:
                new_team_lead = User.objects.get(id=lead_id, is_active=True)
                validated_data['team_lead'] = new_team_lead
                
                # Actualizar rol del nuevo líder si es necesario
                try:
                    new_profile = new_team_lead.hps_profile
                    current_role_name = new_profile.role.name if new_profile.role else None
                    
                    # Si el rol actual es "member", cambiar a "team_lead"
                    if current_role_name == "member":
                        team_lead_role = models.HpsRole.objects.filter(name="team_lead").first()
                        if team_lead_role:
                            new_profile.role = team_lead_role
                            new_profile.save(update_fields=['role'])
                            logger.info(f"Usuario {new_team_lead.email} cambió de 'member' a 'team_lead' al asignarle liderazgo")
                    # Si tiene otro rol (crypto, admin, etc.), mantenerlo
                    elif current_role_name and current_role_name != "team_lead":
                        logger.info(f"Usuario {new_team_lead.email} mantiene rol '{current_role_name}' pero tiene permisos de líder de equipo")
                except models.HpsUserProfile.DoesNotExist:
                    logger.warning(f"Usuario {new_team_lead.email} no tiene perfil HPS")
                    
            except User.DoesNotExist:
                raise serializers.ValidationError({'team_lead_id_writable': f'Usuario con ID {lead_id} no existe o está inactivo'})
        else:
            validated_data['team_lead'] = None
        
        return super().create(validated_data)
    
    def validate_team_lead_id_writable(self, value):
        """Validar que el usuario existe si se proporciona team_lead_id_writable"""
        if value is not None and value != '':
            try:
                User.objects.get(id=value, is_active=True)
            except User.DoesNotExist:
                raise serializers.ValidationError(f'Usuario con ID {value} no existe o está inactivo')
        return value
    
    def update(self, instance, validated_data):
        """
        Actualizar equipo, manejando team_lead_id_writable y actualizando roles de usuarios.
        
        Lógica de asignación de líder:
        - Si el usuario tiene rol "member" y se le asigna como líder, cambiar a "team_lead"
        - Si el usuario tiene otro rol (crypto, admin, etc.), mantenerlo pero internamente tiene permisos de líder
        - Si se quita el liderazgo y el rol era "team_lead", volver a "member"
        """
        import logging
        logger = logging.getLogger(__name__)
        
        team_lead_id_writable = validated_data.pop('team_lead_id_writable', None)
        # También aceptar team_lead_id para compatibilidad
        team_lead_id = validated_data.pop('team_lead_id', None)
        
        # Usar team_lead_id_writable si está presente, sino team_lead_id
        lead_id = team_lead_id_writable if team_lead_id_writable is not None else team_lead_id
        
        # Guardar el líder anterior para poder revertir cambios si es necesario
        old_team_lead = instance.team_lead
        
        if lead_id is not None:
            if lead_id == '' or lead_id is None:
                # Se está quitando el liderazgo
                if old_team_lead:
                    try:
                        old_profile = old_team_lead.hps_profile
                        # Si el rol era "team_lead", volver a "member"
                        if old_profile.role and old_profile.role.name == "team_lead":
                            member_role = models.HpsRole.objects.filter(name="member").first()
                            if member_role:
                                old_profile.role = member_role
                                old_profile.save(update_fields=['role'])
                                logger.info(f"Usuario {old_team_lead.email} vuelve a rol 'member' al quitarle el liderazgo")
                    except models.HpsUserProfile.DoesNotExist:
                        pass
                instance.team_lead = None
            else:
                # Se está asignando un nuevo líder
                try:
                    new_team_lead = User.objects.get(id=lead_id, is_active=True)
                    instance.team_lead = new_team_lead
                    
                    # Actualizar rol del nuevo líder si es necesario
                    try:
                        new_profile = new_team_lead.hps_profile
                        current_role_name = new_profile.role.name if new_profile.role else None
                        
                        # Si el rol actual es "member", cambiar a "team_lead"
                        if current_role_name == "member":
                            team_lead_role = models.HpsRole.objects.filter(name="team_lead").first()
                            if team_lead_role:
                                new_profile.role = team_lead_role
                                new_profile.save(update_fields=['role'])
                                logger.info(f"Usuario {new_team_lead.email} cambió de 'member' a 'team_lead' al asignarle liderazgo")
                        # Si tiene otro rol (crypto, admin, etc.), mantenerlo
                        # Los permisos se manejan en el sistema de permisos que verifica si es team_lead del equipo
                        elif current_role_name and current_role_name != "team_lead":
                            logger.info(f"Usuario {new_team_lead.email} mantiene rol '{current_role_name}' pero tiene permisos de líder de equipo")
                    except models.HpsUserProfile.DoesNotExist:
                        logger.warning(f"Usuario {new_team_lead.email} no tiene perfil HPS")
                    
                    # Si había un líder anterior diferente, revertir su rol si era "team_lead"
                    if old_team_lead and old_team_lead.id != new_team_lead.id:
                        try:
                            old_profile = old_team_lead.hps_profile
                            if old_profile.role and old_profile.role.name == "team_lead":
                                member_role = models.HpsRole.objects.filter(name="member").first()
                                if member_role:
                                    old_profile.role = member_role
                                    old_profile.save(update_fields=['role'])
                                    logger.info(f"Usuario {old_team_lead.email} vuelve a rol 'member' al quitarle el liderazgo")
                        except models.HpsUserProfile.DoesNotExist:
                            pass
                            
                except User.DoesNotExist:
                    raise serializers.ValidationError({'team_lead_id_writable': f'Usuario con ID {lead_id} no existe o está inactivo'})
        
        # Actualizar otros campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class HpsRequestSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    submitted_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    approved_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), allow_null=True, required=False
    )
    # Campos calculados
    is_expired = serializers.BooleanField(read_only=True)
    can_be_approved = serializers.SerializerMethodField()
    # Campo 'type' como alias de 'form_type' para compatibilidad con frontend
    type = serializers.CharField(source='form_type', read_only=True)
    # URLs de PDFs
    filled_pdf_url = serializers.SerializerMethodField()
    response_pdf_url = serializers.SerializerMethodField()
    template_pdf_url = serializers.SerializerMethodField()
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
    
    def validate_form_type(self, value):
        """Validar y normalizar form_type"""
        if not value:
            return models.HpsRequest.FormType.SOLICITUD
        
        value_lower = value.lower().strip()
        # Normalizar valores comunes a "solicitud" o "traslado"
        if value_lower in ["traslado", "traspaso", "transfer", "trasladar", "traspasar"]:
            return models.HpsRequest.FormType.TRASLADO
        else:
            # Cualquier otro valor (incluyendo "nueva", "new", "solicitud", etc.) se convierte a "solicitud"
            return models.HpsRequest.FormType.SOLICITUD
    
    def get_can_be_approved(self, obj):
        """Verifica si la solicitud puede ser aprobada"""
        return obj.status == 'pending' and not obj.is_expired
    
    def get_user_full_name(self, obj):
        """Obtiene el nombre completo del usuario"""
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return ""
    
    def get_filled_pdf_url(self, obj):
        """Obtener URL del PDF rellenado"""
        if obj.filled_pdf:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.filled_pdf.url)
            return obj.filled_pdf.url
        return None
    
    def get_response_pdf_url(self, obj):
        """Obtener URL del PDF de respuesta"""
        if obj.response_pdf:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.response_pdf.url)
            return obj.response_pdf.url
        return None
    
    def get_template_pdf_url(self, obj):
        """Obtener URL del PDF de la plantilla asociada"""
        if obj.template and obj.template.template_pdf:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.template.template_pdf.url)
            return obj.template.template_pdf.url
        return None


class HpsTemplateSerializer(serializers.ModelSerializer):
    """Serializer para plantillas PDF de HPS"""
    template_pdf_url = serializers.SerializerMethodField()
    
    class Meta:
        model = models.HpsTemplate
        fields = [
            "id",
            "name",
            "description",
            "template_pdf",
            "template_pdf_url",
            "template_type",
            "version",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
    
    def get_template_pdf_url(self, obj):
        """Obtener URL del PDF de la plantilla"""
        if obj.template_pdf:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.template_pdf.url)
            return obj.template_pdf.url
        return None


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
    # Campo escribible para actualizar el rol (acepta el nombre del rol como string)
    role_writable = serializers.CharField(write_only=True, required=False, allow_blank=True)
    team_id = serializers.SerializerMethodField()
    team_name = serializers.CharField(source='team.name', read_only=True, allow_null=True)
    # Campo escribible para actualizar el equipo (acepta UUID como string)
    team_id_writable = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    hps_requests_count = serializers.SerializerMethodField()
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
            "role_writable",
            "team_id",
            "team_name",
            "team_id_writable",
            "is_active",
            "is_temp_password",
            "must_change_password",
            "email_verified",
            "hps_requests_count",
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
    
    def get_hps_requests_count(self, obj):
        """Obtiene el número de solicitudes HPS asociadas al usuario"""
        if obj.user:
            return models.HpsRequest.objects.filter(user=obj.user).count()
        return 0
    
    def _get_or_create_aicox_team(self):
        """
        Obtener o crear el equipo AICOX.
        Retorna el equipo AICOX, creándolo si no existe.
        """
        import uuid
        AICOX_TEAM_UUID = uuid.UUID('d8574c01-851f-4716-9ac9-bbda45469bdf')
        
        try:
            # Intentar obtener el equipo por UUID
            team = models.HpsTeam.objects.get(id=AICOX_TEAM_UUID)
            return team
        except models.HpsTeam.DoesNotExist:
            # Si no existe, intentar obtenerlo por nombre
            team = models.HpsTeam.objects.filter(name__iexact='AICOX').first()
            if team:
                return team
            
            # Crear el equipo AICOX
            team = models.HpsTeam.objects.create(
                id=AICOX_TEAM_UUID,
                name='AICOX',
                description='Equipo genérico AICOX',
                is_active=True
            )
            return team
    
    def create(self, validated_data):
        """Crear un nuevo perfil de usuario HPS con el rol especificado"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Extraer datos del usuario
        email = validated_data.pop('email', None) or validated_data.pop('user', {}).get('email')
        username = validated_data.pop('username', None) or email
        password = validated_data.pop('password', None)
        first_name = validated_data.pop('first_name', None) or validated_data.pop('user', {}).get('first_name', '')
        last_name = validated_data.pop('last_name', None) or validated_data.pop('user', {}).get('last_name', '')
        full_name = validated_data.pop('full_name', None)
        
        # Si se proporciona full_name, dividirlo en first_name y last_name
        if full_name and not first_name:
            name_parts = full_name.strip().split(' ', 1)
            first_name = name_parts[0] if len(name_parts) > 0 else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Manejar rol
        role_writable = validated_data.pop('role_writable', None)
        role = None
        if role_writable:
            try:
                role = models.HpsRole.objects.get(name=role_writable)
            except models.HpsRole.DoesNotExist:
                raise serializers.ValidationError({'role_writable': f'El rol "{role_writable}" no existe'})
        else:
            # Rol por defecto: "member"
            role = models.HpsRole.objects.filter(name="member").first()
            if not role:
                role, _ = models.HpsRole.objects.get_or_create(
                    name="crypto",
                    defaults={"description": "Perfil base para usuarios de CryptoTrace", "permissions": {}}
                )
        
        # Manejar equipo
        team_id_writable = validated_data.pop('team_id_writable', None)
        team = None
        if team_id_writable:
            try:
                import uuid
                team_uuid = uuid.UUID(team_id_writable)
                team = models.HpsTeam.objects.get(id=team_uuid)
            except (ValueError, models.HpsTeam.DoesNotExist):
                raise serializers.ValidationError({'team_id_writable': f'El equipo con ID "{team_id_writable}" no existe'})
        else:
            # Si no se especifica equipo, asignar automáticamente al equipo AICOX
            team = self._get_or_create_aicox_team()
        
        # Crear o obtener usuario
        if email:
            user, user_created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': username or email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_active': True,
                }
            )
            
            if user_created and password:
                user.set_password(password)
                user.save()
            elif password:
                # Actualizar contraseña si se proporciona
                user.set_password(password)
                user.save()
            
            # Actualizar nombre si se proporcionó
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if username and user.username != username:
                user.username = username
            user.save()
        else:
            raise serializers.ValidationError({'email': 'El email es requerido para crear un usuario'})
        
        # Crear o actualizar perfil HPS
        profile, profile_created = models.HpsUserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': role,
                'team': team,
                **validated_data
            }
        )
        
        if not profile_created:
            # Actualizar perfil existente
            profile.role = role
            if team is not None:
                profile.team = team
            for attr, value in validated_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return profile
    
    def validate_role_writable(self, value):
        """Validar que el rol existe"""
        if value:
            try:
                role = models.HpsRole.objects.get(name=value)
                return value
            except models.HpsRole.DoesNotExist:
                raise serializers.ValidationError(f'El rol "{value}" no existe')
        return value
    
    def validate_team_id_writable(self, value):
        """Validar que el equipo existe si se proporciona"""
        if value:
            try:
                import uuid
                team_uuid = uuid.UUID(value)
                team = models.HpsTeam.objects.get(id=team_uuid)
                return value
            except (ValueError, models.HpsTeam.DoesNotExist):
                raise serializers.ValidationError(f'El equipo con ID "{value}" no existe')
        return value
    
    def update(self, instance, validated_data):
        """Actualizar el perfil, incluyendo el rol y el equipo si se proporcionan"""
        # Manejar actualización del rol
        role_writable = validated_data.pop('role_writable', None)
        if role_writable:
            try:
                role = models.HpsRole.objects.get(name=role_writable)
                instance.role = role
            except models.HpsRole.DoesNotExist:
                raise serializers.ValidationError({'role_writable': f'El rol "{role_writable}" no existe'})
        
        # Manejar actualización del equipo
        team_id_writable = validated_data.pop('team_id_writable', None)
        if team_id_writable is not None:  # Permite establecer a None explícitamente
            if team_id_writable == '' or team_id_writable is None:
                # Si se establece explícitamente a None, asignar al equipo AICOX por defecto
                instance.team = self._get_or_create_aicox_team()
            else:
                try:
                    import uuid
                    team_uuid = uuid.UUID(team_id_writable)
                    team = models.HpsTeam.objects.get(id=team_uuid)
                    instance.team = team
                except (ValueError, models.HpsTeam.DoesNotExist):
                    raise serializers.ValidationError({'team_id_writable': f'El equipo con ID "{team_id_writable}" no existe'})
        else:
            # Si no se especifica equipo y el usuario no tiene uno, asignar automáticamente al equipo AICOX
            if not instance.team:
                instance.team = self._get_or_create_aicox_team()
        
        # Actualizar otros campos del perfil
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class ChatConversationSerializer(serializers.ModelSerializer):
    """Serializer para conversaciones de chat"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    class Meta:
        model = models.ChatConversation
        fields = [
            "id",
            "user",
            "user_id",
            "user_email",
            "user_first_name",
            "user_last_name",
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

