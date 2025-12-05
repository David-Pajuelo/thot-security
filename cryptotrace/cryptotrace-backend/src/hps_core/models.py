import uuid
from datetime import date

from django.conf import settings
from django.db import models
from django.utils import timezone


class HpsRole(models.Model):
    """
    Equivalente Django del modelo SQLAlchemy ``Role``.

    Mantiene permisos y metadatos específicos del dominio HPS sin interferir
    con los grupos/roles nativos de Django hasta completar la migración.
    """

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Rol HPS"
        verbose_name_plural = "Roles HPS"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class HpsTeam(models.Model):
    """
    Equipos operativos y cadenas de mando para solicitudes HPS.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    team_lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="hps_led_teams",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Equipo HPS"
        verbose_name_plural = "Equipos HPS"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def is_team_lead(self, user_id: uuid.UUID) -> bool:
        return str(self.team_lead_id) == str(user_id)

    @property
    def member_count(self) -> int:
        """
        Contar miembros del equipo a través de HpsUserProfile.
        Los usuarios están asociados al equipo mediante HpsUserProfile.team.
        """
        from .models import HpsUserProfile
        return HpsUserProfile.objects.filter(
            team=self,
            user__is_active=True
        ).count()


class HpsTeamMembership(models.Model):
    """
    Asociación explícita entre usuarios de Django y equipos HPS.
    Reemplaza el ``team_id`` directo que existía en el modelo FastAPI.
    """

    team = models.ForeignKey(
        HpsTeam, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hps_team_memberships",
    )
    is_active = models.BooleanField(default=True)
    is_lead = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Membresía de equipo HPS"
        verbose_name_plural = "Membresías de equipo HPS"
        unique_together = ("team", "user")

    def __str__(self) -> str:
        return f"{self.user} @ {self.team}"


class HpsUserProfile(models.Model):
    """
    Perfil extendido para mapear la información adicional que el backend HPS
    almacenaba en ``src.models.user.User``.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hps_profile",
    )
    role = models.ForeignKey(
        HpsRole, on_delete=models.PROTECT, related_name="profiles"
    )
    team = models.ForeignKey(
        HpsTeam,
        on_delete=models.SET_NULL,
        related_name="profiles",
        null=True,
        blank=True,
    )
    email_verified = models.BooleanField(default=False)
    is_temp_password = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    extra_permissions = models.JSONField(default=dict, blank=True)
    must_change_password = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Perfil de usuario HPS"
        verbose_name_plural = "Perfiles de usuario HPS"

    def __str__(self) -> str:
        return f"HPS Profile for {self.user}"


class HpsTemplate(models.Model):
    """
    Plantillas PDF empleadas para generar documentación HPS.
    """

    class TemplateType(models.TextChoices):
        JEFE = "jefe_seguridad", "Jefe de seguridad"
        SUPLENTE = "jefe_seguridad_suplente", "Jefe suplente"

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    template_pdf = models.FileField(upload_to="hps/templates/")
    template_type = models.CharField(
        max_length=50, choices=TemplateType.choices, default=TemplateType.JEFE
    )
    version = models.CharField(max_length=50, default="1.0")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Plantilla HPS"
        verbose_name_plural = "Plantillas HPS"
        ordering = ["name", "version"]

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"


class HpsRequest(models.Model):
    """
    Traslado del modelo ``HPSRequest`` completo hacia Django.
    """

    class RequestStatus(models.TextChoices):
        PENDING = "pending", "Pendiente"
        WAITING_DPS = "waiting_dps", "Esperando DPS"
        SUBMITTED = "submitted", "Enviada"
        APPROVED = "approved", "Aprobada"
        REJECTED = "rejected", "Rechazada"
        EXPIRED = "expired", "Expirada"

    class RequestType(models.TextChoices):
        NEW = "new", "Alta"
        RENEWAL = "renewal", "Renovación"
        TRANSFER = "transfer", "Traslado"

    class FormType(models.TextChoices):
        SOLICITUD = "solicitud", "Solicitud"
        TRASLADO = "traslado", "Traslado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="hps_requests",
        null=True,
        blank=True,
    )
    request_type = models.CharField(
        max_length=50, choices=RequestType.choices, default=RequestType.NEW
    )
    status = models.CharField(
        max_length=50, choices=RequestStatus.choices, default=RequestStatus.PENDING
    )
    form_type = models.CharField(
        max_length=20, choices=FormType.choices, default=FormType.SOLICITUD
    )
    template = models.ForeignKey(
        HpsTemplate, on_delete=models.SET_NULL, null=True, blank=True
    )
    filled_pdf = models.FileField(upload_to="hps/filled/", null=True, blank=True)
    response_pdf = models.FileField(upload_to="hps/responses/", null=True, blank=True)

    document_type = models.CharField(max_length=50)
    document_number = models.CharField(max_length=50)
    birth_date = models.DateField()
    first_name = models.CharField(max_length=100)
    first_last_name = models.CharField(max_length=100)
    second_last_name = models.CharField(max_length=100, blank=True)
    nationality = models.CharField(max_length=100)
    birth_place = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50)

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="submitted_hps_requests",
        null=True,
        blank=True,
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="approved_hps_requests",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    security_clearance_level = models.CharField(max_length=255, blank=True)
    government_expediente = models.CharField(max_length=50, blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    company_nif = models.CharField(max_length=20, blank=True)
    internal_code = models.CharField(max_length=50, blank=True)
    job_position = models.CharField(max_length=100, blank=True)
    auto_processed = models.BooleanField(default=False)
    source_pdf_filename = models.CharField(max_length=255, blank=True)
    auto_processed_at = models.DateTimeField(null=True, blank=True)
    government_document_type = models.CharField(max_length=100, blank=True)
    data_source = models.CharField(max_length=50, default="manual", blank=True)
    original_status_text = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Solicitud HPS"
        verbose_name_plural = "Solicitudes HPS"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["request_type"]),
            models.Index(fields=["government_expediente"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"HPS {self.document_number} ({self.get_status_display()})"

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return self.expires_at < date.today()

    def approve(self, approved_by_user, expires_at=None):
        self.status = self.RequestStatus.APPROVED
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        if expires_at:
            self.expires_at = expires_at

    def reject(self, approved_by_user, notes=""):
        self.status = self.RequestStatus.REJECTED
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        if notes:
            self.notes = notes


class HpsToken(models.Model):
    """
    Tokens seguros para exponer formularios públicos de HPS.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=255, unique=True)
    email = models.EmailField()
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="requested_hps_tokens",
    )
    purpose = models.CharField(max_length=500, blank=True)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Token HPS"
        verbose_name_plural = "Tokens HPS"
        indexes = [models.Index(fields=["token"]), models.Index(fields=["expires_at"])]

    def __str__(self) -> str:
        return f"Token HPS for {self.email}"

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_used and not self.is_expired
    
    @classmethod
    def generate_secure_token(cls) -> str:
        """Generar token seguro único"""
        import secrets
        return f"{uuid.uuid4().hex}{secrets.token_urlsafe(32)}"
    
    @classmethod
    def create_token(cls, email: str, requested_by_user, purpose: str = None, hours_valid: int = 72):
        """
        Crear un nuevo token HPS
        
        Args:
            email: Email del destinatario
            requested_by_user: Usuario que solicita
            purpose: Motivo de la solicitud
            hours_valid: Horas de validez (por defecto 72h)
        """
        from datetime import timedelta
        return cls.objects.create(
            token=cls.generate_secure_token(),
            email=email,
            requested_by=requested_by_user,
            purpose=purpose or "",
            expires_at=timezone.now() + timedelta(hours=hours_valid)
        )


class HpsAuditLog(models.Model):
    """
    Bitácora de cambios del sistema HPS.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="hps_audit_logs",
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=100)
    table_name = models.CharField(max_length=100, blank=True)
    record_id = models.UUIDField(null=True, blank=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log de auditoría HPS"
        verbose_name_plural = "Logs de auditoría HPS"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.action} @ {self.created_at:%Y-%m-%d %H:%M:%S}"


class HpsUserMapping(models.Model):
    """
    Tabla de mapeo para mantener referencia entre UUIDs de usuarios HPS
    y los IDs de usuarios Django después de la migración.
    """
    hps_user_uuid = models.UUIDField(unique=True, db_index=True)
    django_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hps_mapping"
    )
    migrated_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Mapeo de Usuario HPS"
        verbose_name_plural = "Mapeos de Usuarios HPS"
        ordering = ["-migrated_at"]

    def __str__(self) -> str:
        return f"HPS UUID {self.hps_user_uuid} → User {self.django_user.id}"


class ChatConversation(models.Model):
    """
    Conversaciones de chat con el agente IA.
    Migrado desde hps-system.
    """
    
    class ConversationStatus(models.TextChoices):
        ACTIVE = "active", "Activa"
        CLOSED = "closed", "Cerrada"
        ARCHIVED = "archived", "Archivada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_conversations"
    )
    session_id = models.CharField(max_length=255, db_index=True)
    title = models.CharField(max_length=500, blank=True)
    status = models.CharField(
        max_length=50,
        choices=ConversationStatus.choices,
        default=ConversationStatus.ACTIVE
    )
    total_messages = models.IntegerField(default=0)
    total_tokens_used = models.IntegerField(default=0)
    conversation_data = models.JSONField(null=True, blank=True)  # Almacena conversación completa
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Conversación de Chat"
        verbose_name_plural = "Conversaciones de Chat"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["session_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"Chat {self.session_id} - {self.user.email} ({self.get_status_display()})"


class ChatMessage(models.Model):
    """
    Mensajes individuales dentro de una conversación de chat.
    Migrado desde hps-system.
    """
    
    class MessageType(models.TextChoices):
        USER = "user", "Usuario"
        ASSISTANT = "assistant", "Asistente"
        SYSTEM = "system", "Sistema"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        ChatConversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    message_type = models.CharField(
        max_length=50,
        choices=MessageType.choices
    )
    content = models.TextField()
    tokens_used = models.IntegerField(default=0)
    response_time_ms = models.IntegerField(null=True, blank=True)
    is_error = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    message_metadata = models.TextField(blank=True)  # JSON string con metadatos
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mensaje de Chat"
        verbose_name_plural = "Mensajes de Chat"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
            models.Index(fields=["message_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_message_type_display()} @ {self.created_at:%Y-%m-%d %H:%M:%S}"


class ChatMetrics(models.Model):
    """
    Métricas agregadas del sistema de chat.
    Migrado desde hps-system.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateTimeField(db_index=True)
    total_conversations = models.IntegerField(default=0)
    total_messages = models.IntegerField(default=0)
    total_tokens_used = models.IntegerField(default=0)
    avg_response_time_ms = models.FloatField(default=0.0)
    avg_satisfaction_rating = models.FloatField(default=0.0)
    error_rate = models.FloatField(default=0.0)
    active_users = models.IntegerField(default=0)
    peak_concurrent_users = models.IntegerField(default=0)
    most_common_topics = models.TextField(blank=True)  # JSON string
    system_health_score = models.FloatField(default=100.0)  # 0-100
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Métrica de Chat"
        verbose_name_plural = "Métricas de Chat"
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["date"]),
        ]

    def __str__(self) -> str:
        return f"Métricas {self.date:%Y-%m-%d} - {self.total_conversations} conversaciones"

