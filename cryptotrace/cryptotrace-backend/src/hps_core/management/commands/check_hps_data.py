"""
Script para verificar qué datos de HPS existen actualmente en la base de datos.
"""
from django.core.management.base import BaseCommand
from hps_core.models import (
    HpsRole, HpsTeam, HpsTeamMembership, HpsUserProfile,
    HpsTemplate, HpsRequest, HpsToken, HpsAuditLog,
    ChatConversation, ChatMessage, ChatMetrics, HpsUserMapping
)
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Verifica qué datos de HPS existen en la base de datos actual'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('VERIFICACIÓN DE DATOS HPS EN CRYPTOTRACE'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # Roles
        roles_count = HpsRole.objects.count()
        self.stdout.write(f'\n📋 Roles HPS: {roles_count}')
        if roles_count > 0:
            for role in HpsRole.objects.all()[:5]:
                self.stdout.write(f'   - {role.name}')
            if roles_count > 5:
                self.stdout.write(f'   ... y {roles_count - 5} más')
        
        # Equipos
        teams_count = HpsTeam.objects.count()
        self.stdout.write(f'\n👥 Equipos HPS: {teams_count}')
        if teams_count > 0:
            for team in HpsTeam.objects.all()[:5]:
                self.stdout.write(f'   - {team.name} (Líder: {team.team_lead.email if team.team_lead else "N/A"})')
            if teams_count > 5:
                self.stdout.write(f'   ... y {teams_count - 5} más')
        
        # Membresías de equipos
        memberships_count = HpsTeamMembership.objects.count()
        self.stdout.write(f'\n🔗 Membresías de equipos: {memberships_count}')
        
        # Perfiles de usuario HPS
        profiles_count = HpsUserProfile.objects.count()
        self.stdout.write(f'\n👤 Perfiles de usuario HPS: {profiles_count}')
        if profiles_count > 0:
            for profile in HpsUserProfile.objects.select_related('user', 'role', 'team').all()[:5]:
                self.stdout.write(f'   - {profile.user.email} (Rol: {profile.role.name}, Equipo: {profile.team.name if profile.team else "N/A"})')
            if profiles_count > 5:
                self.stdout.write(f'   ... y {profiles_count - 5} más')
        
        # Plantillas
        templates_count = HpsTemplate.objects.count()
        self.stdout.write(f'\n📄 Plantillas HPS: {templates_count}')
        if templates_count > 0:
            for template in HpsTemplate.objects.all()[:5]:
                has_pdf = bool(template.template_pdf)
                self.stdout.write(f'   - {template.name} v{template.version} (PDF: {"Sí" if has_pdf else "No"})')
            if templates_count > 5:
                self.stdout.write(f'   ... y {templates_count - 5} más')
        
        # Solicitudes HPS
        requests_count = HpsRequest.objects.count()
        self.stdout.write(f'\n📝 Solicitudes HPS: {requests_count}')
        if requests_count > 0:
            # Estadísticas por estado
            pending = HpsRequest.objects.filter(status='pending').count()
            approved = HpsRequest.objects.filter(status='approved').count()
            rejected = HpsRequest.objects.filter(status='rejected').count()
            self.stdout.write(f'   - Pendientes: {pending}')
            self.stdout.write(f'   - Aprobadas: {approved}')
            self.stdout.write(f'   - Rechazadas: {rejected}')
            # Con PDFs
            with_filled = HpsRequest.objects.exclude(filled_pdf='').count()
            with_response = HpsRequest.objects.exclude(response_pdf='').count()
            self.stdout.write(f'   - Con filled_pdf: {with_filled}')
            self.stdout.write(f'   - Con response_pdf: {with_response}')
        
        # Tokens
        tokens_count = HpsToken.objects.count()
        self.stdout.write(f'\n🔑 Tokens HPS: {tokens_count}')
        if tokens_count > 0:
            used = HpsToken.objects.filter(is_used=True).count()
            expired = HpsToken.objects.filter(is_used=False).count()  # Simplificado
            self.stdout.write(f'   - Usados: {used}')
            self.stdout.write(f'   - No usados: {tokens_count - used}')
        
        # Logs de auditoría
        audit_logs_count = HpsAuditLog.objects.count()
        self.stdout.write(f'\n📊 Logs de auditoría HPS: {audit_logs_count}')
        
        # Chat (puede que las tablas no existan aún)
        try:
            conversations_count = ChatConversation.objects.count()
            messages_count = ChatMessage.objects.count()
            metrics_count = ChatMetrics.objects.count()
            self.stdout.write(f'\n💬 Chat:')
            self.stdout.write(f'   - Conversaciones: {conversations_count}')
            self.stdout.write(f'   - Mensajes: {messages_count}')
            self.stdout.write(f'   - Métricas: {metrics_count}')
        except Exception as e:
            self.stdout.write(f'\n💬 Chat: (tablas no creadas aún - ejecutar migrate)')
        
        # Mapeo de usuarios
        mappings_count = HpsUserMapping.objects.count()
        self.stdout.write(f'\n🗺️  Mapeos de usuarios (HPS → Django): {mappings_count}')
        
        # Usuarios Django con perfil HPS
        users_with_hps = User.objects.filter(hps_profile__isnull=False).count()
        total_users = User.objects.count()
        self.stdout.write(f'\n👥 Usuarios Django:')
        self.stdout.write(f'   - Total: {total_users}')
        self.stdout.write(f'   - Con perfil HPS: {users_with_hps}')
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('Verificación completada'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

