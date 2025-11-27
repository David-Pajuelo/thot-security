from django.contrib import admin
from . import models


@admin.register(models.HpsRole)
class HpsRoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['created_at']


@admin.register(models.HpsTeam)
class HpsTeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'team_lead', 'is_active', 'member_count', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['is_active', 'created_at']
    raw_id_fields = ['team_lead']


@admin.register(models.HpsTeamMembership)
class HpsTeamMembershipAdmin(admin.ModelAdmin):
    list_display = ['team', 'user', 'is_active', 'is_lead', 'created_at']
    list_filter = ['is_active', 'is_lead', 'created_at']
    raw_id_fields = ['team', 'user']
    search_fields = ['user__username', 'user__email', 'team__name']


@admin.register(models.HpsUserProfile)
class HpsUserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'team', 'must_change_password', 'email_verified', 'is_temp_password']
    list_filter = ['role', 'must_change_password', 'email_verified', 'is_temp_password']
    raw_id_fields = ['user', 'role', 'team']
    search_fields = ['user__username', 'user__email']


@admin.register(models.HpsTemplate)
class HpsTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'version', 'active', 'created_at']
    list_filter = ['template_type', 'active', 'created_at']
    search_fields = ['name', 'description']


@admin.register(models.HpsRequest)
class HpsRequestAdmin(admin.ModelAdmin):
    list_display = [
        'document_number', 'first_name', 'first_last_name', 
        'request_type', 'status', 'form_type', 'submitted_at', 'created_at'
    ]
    list_filter = ['status', 'request_type', 'form_type', 'submitted_at', 'created_at']
    search_fields = [
        'document_number', 'first_name', 'first_last_name', 
        'email', 'phone', 'government_expediente'
    ]
    raw_id_fields = ['user', 'submitted_by', 'approved_by', 'template']
    readonly_fields = ['created_at', 'updated_at', 'submitted_at', 'approved_at', 'auto_processed_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información Personal', {
            'fields': (
                'document_type', 'document_number', 'birth_date',
                'first_name', 'first_last_name', 'second_last_name',
                'nationality', 'birth_place', 'email', 'phone'
            )
        }),
        ('Solicitud', {
            'fields': (
                'user', 'request_type', 'status', 'form_type',
                'template', 'submitted_by', 'submitted_at',
                'approved_by', 'approved_at', 'expires_at', 'notes'
            )
        }),
        ('Documentos', {
            'fields': ('filled_pdf', 'response_pdf'),
            'classes': ('collapse',)
        }),
        ('Información Adicional', {
            'fields': (
                'security_clearance_level', 'government_expediente',
                'company_name', 'company_nif', 'internal_code', 'job_position'
            ),
            'classes': ('collapse',)
        }),
        ('Procesamiento Automático', {
            'fields': (
                'auto_processed', 'source_pdf_filename', 'auto_processed_at',
                'government_document_type', 'data_source', 'original_status_text'
            ),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(models.HpsToken)
class HpsTokenAdmin(admin.ModelAdmin):
    list_display = ['email', 'requested_by', 'is_used', 'is_expired', 'expires_at', 'created_at']
    list_filter = ['is_used', 'expires_at', 'created_at']
    search_fields = ['email', 'token', 'purpose']
    raw_id_fields = ['requested_by']
    readonly_fields = ['token', 'is_expired', 'is_valid', 'created_at', 'updated_at', 'used_at']
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expirado'
    
    def is_valid(self, obj):
        return obj.is_valid
    is_valid.boolean = True
    is_valid.short_description = 'Válido'


@admin.register(models.HpsAuditLog)
class HpsAuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'user', 'table_name', 'created_at']
    list_filter = ['action', 'table_name', 'created_at']
    search_fields = ['action', 'table_name', 'user__username', 'user__email']
    raw_id_fields = ['user']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(models.HpsUserMapping)
class HpsUserMappingAdmin(admin.ModelAdmin):
    list_display = ['hps_user_uuid', 'django_user', 'migrated_at']
    list_filter = ['migrated_at']
    search_fields = ['hps_user_uuid', 'django_user__username', 'django_user__email']
    raw_id_fields = ['django_user']
    readonly_fields = ['migrated_at']
    date_hierarchy = 'migrated_at'


@admin.register(models.ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'title', 'status', 'total_messages', 'total_tokens_used', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['session_id', 'title', 'user__username', 'user__email']
    raw_id_fields = ['user']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'closed_at']
    date_hierarchy = 'created_at'


@admin.register(models.ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'message_type', 'is_error', 'tokens_used', 'created_at']
    list_filter = ['message_type', 'is_error', 'created_at']
    search_fields = ['content', 'conversation__session_id']
    raw_id_fields = ['conversation']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(models.ChatMetrics)
class ChatMetricsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_conversations', 'total_messages', 'total_tokens_used', 'active_users', 'system_health_score']
    list_filter = ['date']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'

