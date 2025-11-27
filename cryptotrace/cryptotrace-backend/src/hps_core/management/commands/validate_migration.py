"""
Script de validación post-migración.

Valida que todos los datos se hayan migrado correctamente comparando
conteos y verificando integridad referencial.
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from hps_core.models import (
    HpsRole, HpsTeam, HpsUserProfile, HpsTemplate,
    HpsRequest, HpsToken, HpsAuditLog, HpsUserMapping,
    ChatConversation, ChatMessage, ChatMetrics
)
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Valida la migración comparando datos de hps-system con Django'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hps-db-url',
            type=str,
            required=True,
            help='URL de conexión a base HPS: postgresql://user:pass@host:port/dbname'
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Mostrar detalles de discrepancias'
        )

    def handle(self, *args, **options):
        hps_db_url = options['hps_db_url']
        detailed = options['detailed']

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('VALIDACIÓN DE MIGRACIÓN'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # Conectar a base HPS
        try:
            hps_conn = psycopg2.connect(hps_db_url)
            hps_cursor = hps_conn.cursor(cursor_factory=RealDictCursor)
            self.stdout.write(self.style.SUCCESS('\n✓ Conectado a base HPS\n'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error conectando a base HPS: {str(e)}'))
            return

        validation_errors = []
        validation_warnings = []

        try:
            # ===== Validar Roles =====
            self.stdout.write('📋 Validando Roles...')
            try:
                hps_cursor.execute("SELECT COUNT(*) as count FROM roles")
                hps_roles = hps_cursor.fetchone()['count']
                django_roles = HpsRole.objects.count()
                
                if hps_roles == django_roles:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Roles: {django_roles}/{hps_roles}'))
                else:
                    validation_errors.append(f'Roles: {django_roles} en Django vs {hps_roles} en HPS')
                    self.stdout.write(self.style.ERROR(f'  ✗ Roles: {django_roles} en Django vs {hps_roles} en HPS'))
            except Exception as e:
                validation_warnings.append(f'Roles: Error verificando - {str(e)}')
                self.stdout.write(self.style.WARNING(f'  ⚠ Roles: Error - {str(e)}'))

            # ===== Validar Usuarios =====
            self.stdout.write('\n👤 Validando Usuarios...')
            try:
                hps_cursor.execute("SELECT COUNT(*) as count FROM users")
                hps_users = hps_cursor.fetchone()['count']
                django_users = User.objects.count()
                django_profiles = HpsUserProfile.objects.count()
                mappings = HpsUserMapping.objects.count()
                
                self.stdout.write(f'  - HPS usuarios: {hps_users}')
                self.stdout.write(f'  - Django usuarios: {django_users}')
                self.stdout.write(f'  - Perfiles HPS: {django_profiles}')
                self.stdout.write(f'  - Mapeos: {mappings}')
                
                if hps_users == django_users and django_profiles == hps_users:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Usuarios: OK'))
                else:
                    validation_errors.append(f'Usuarios: {django_users} usuarios, {django_profiles} perfiles vs {hps_users} en HPS')
                    self.stdout.write(self.style.ERROR(f'  ✗ Usuarios: Discrepancia'))
            except Exception as e:
                validation_warnings.append(f'Usuarios: Error verificando - {str(e)}')
                self.stdout.write(self.style.WARNING(f'  ⚠ Usuarios: Error - {str(e)}'))

            # ===== Validar Equipos =====
            self.stdout.write('\n👥 Validando Equipos...')
            try:
                hps_cursor.execute("SELECT COUNT(*) as count FROM teams")
                hps_teams = hps_cursor.fetchone()['count']
                django_teams = HpsTeam.objects.count()
                
                if hps_teams == django_teams:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Equipos: {django_teams}/{hps_teams}'))
                else:
                    validation_errors.append(f'Equipos: {django_teams} en Django vs {hps_teams} en HPS')
                    self.stdout.write(self.style.ERROR(f'  ✗ Equipos: {django_teams} en Django vs {hps_teams} en HPS'))
            except Exception as e:
                validation_warnings.append(f'Equipos: Error verificando - {str(e)}')
                self.stdout.write(self.style.WARNING(f'  ⚠ Equipos: Error - {str(e)}'))

            # ===== Validar Plantillas =====
            self.stdout.write('\n📄 Validando Plantillas...')
            try:
                hps_cursor.execute("SELECT COUNT(*) as count FROM hps_templates")
                hps_templates = hps_cursor.fetchone()['count']
                django_templates = HpsTemplate.objects.count()
                
                # Verificar PDFs
                hps_cursor.execute("SELECT COUNT(*) as count FROM hps_templates WHERE template_pdf IS NOT NULL")
                hps_with_pdf = hps_cursor.fetchone()['count']
                django_with_pdf = HpsTemplate.objects.exclude(template_pdf='').count()
                
                if hps_templates == django_templates:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Plantillas: {django_templates}/{hps_templates}'))
                    if hps_with_pdf == django_with_pdf:
                        self.stdout.write(self.style.SUCCESS(f'  ✓ PDFs de plantillas: {django_with_pdf}/{hps_with_pdf}'))
                    else:
                        validation_warnings.append(f'PDFs de plantillas: {django_with_pdf} en Django vs {hps_with_pdf} en HPS')
                        self.stdout.write(self.style.WARNING(f'  ⚠ PDFs de plantillas: {django_with_pdf} vs {hps_with_pdf}'))
                else:
                    validation_errors.append(f'Plantillas: {django_templates} en Django vs {hps_templates} en HPS')
                    self.stdout.write(self.style.ERROR(f'  ✗ Plantillas: {django_templates} en Django vs {hps_templates} en HPS'))
            except Exception as e:
                validation_warnings.append(f'Plantillas: Error verificando - {str(e)}')
                self.stdout.write(self.style.WARNING(f'  ⚠ Plantillas: Error - {str(e)}'))

            # ===== Validar Solicitudes HPS =====
            self.stdout.write('\n📝 Validando Solicitudes HPS...')
            try:
                hps_cursor.execute("SELECT COUNT(*) as count FROM hps_requests")
                hps_requests = hps_cursor.fetchone()['count']
                django_requests = HpsRequest.objects.count()
                
                # PDFs
                hps_cursor.execute("SELECT COUNT(*) as count FROM hps_requests WHERE filled_pdf IS NOT NULL")
                hps_filled = hps_cursor.fetchone()['count']
                django_filled = HpsRequest.objects.exclude(filled_pdf='').count()
                
                hps_cursor.execute("SELECT COUNT(*) as count FROM hps_requests WHERE response_pdf IS NOT NULL")
                hps_response = hps_cursor.fetchone()['count']
                django_response = HpsRequest.objects.exclude(response_pdf='').count()
                
                if hps_requests == django_requests:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Solicitudes: {django_requests}/{hps_requests}'))
                else:
                    validation_errors.append(f'Solicitudes: {django_requests} en Django vs {hps_requests} en HPS')
                    self.stdout.write(self.style.ERROR(f'  ✗ Solicitudes: {django_requests} en Django vs {hps_requests} en HPS'))
                
                self.stdout.write(f'  - filled_pdf: {django_filled}/{hps_filled}')
                self.stdout.write(f'  - response_pdf: {django_response}/{hps_response}')
                
                if django_filled != hps_filled or django_response != hps_response:
                    validation_warnings.append(f'PDFs de solicitudes: filled {django_filled}/{hps_filled}, response {django_response}/{hps_response}')
            except Exception as e:
                validation_warnings.append(f'Solicitudes: Error verificando - {str(e)}')
                self.stdout.write(self.style.WARNING(f'  ⚠ Solicitudes: Error - {str(e)}'))

            # ===== Validar Tokens =====
            self.stdout.write('\n🔑 Validando Tokens...')
            try:
                hps_cursor.execute("SELECT COUNT(*) as count FROM hps_tokens")
                hps_tokens = hps_cursor.fetchone()['count']
                django_tokens = HpsToken.objects.count()
                
                if hps_tokens == django_tokens:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Tokens: {django_tokens}/{hps_tokens}'))
                else:
                    validation_errors.append(f'Tokens: {django_tokens} en Django vs {hps_tokens} en HPS')
                    self.stdout.write(self.style.ERROR(f'  ✗ Tokens: {django_tokens} en Django vs {hps_tokens} en HPS'))
            except Exception as e:
                validation_warnings.append(f'Tokens: Error verificando - {str(e)}')
                self.stdout.write(self.style.WARNING(f'  ⚠ Tokens: Error - {str(e)}'))

            # ===== Validar Logs de Auditoría =====
            self.stdout.write('\n📊 Validando Logs de Auditoría...')
            try:
                hps_cursor.execute("SELECT COUNT(*) as count FROM audit_logs")
                hps_logs = hps_cursor.fetchone()['count']
                django_logs = HpsAuditLog.objects.count()
                
                if hps_logs == django_logs:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Logs: {django_logs}/{hps_logs}'))
                else:
                    validation_errors.append(f'Logs: {django_logs} en Django vs {hps_logs} en HPS')
                    self.stdout.write(self.style.ERROR(f'  ✗ Logs: {django_logs} en Django vs {hps_logs} en HPS'))
            except Exception as e:
                validation_warnings.append(f'Logs: Error verificando - {str(e)}')
                self.stdout.write(self.style.WARNING(f'  ⚠ Logs: Error - {str(e)}'))

            # ===== Validar Chat =====
            self.stdout.write('\n💬 Validando Chat...')
            try:
                hps_cursor.execute("SELECT COUNT(*) as count FROM chat_conversations")
                hps_conversations = hps_cursor.fetchone()['count']
                django_conversations = ChatConversation.objects.count()
                
                hps_cursor.execute("SELECT COUNT(*) as count FROM chat_messages")
                hps_messages = hps_cursor.fetchone()['count']
                django_messages = ChatMessage.objects.count()
                
                hps_cursor.execute("SELECT COUNT(*) as count FROM chat_metrics")
                hps_metrics = hps_cursor.fetchone()['count']
                django_metrics = ChatMetrics.objects.count()
                
                if hps_conversations == django_conversations:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Conversaciones: {django_conversations}/{hps_conversations}'))
                else:
                    validation_errors.append(f'Conversaciones: {django_conversations} en Django vs {hps_conversations} en HPS')
                    self.stdout.write(self.style.ERROR(f'  ✗ Conversaciones: {django_conversations} vs {hps_conversations}'))
                
                if hps_messages == django_messages:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Mensajes: {django_messages}/{hps_messages}'))
                else:
                    validation_errors.append(f'Mensajes: {django_messages} en Django vs {hps_messages} en HPS')
                    self.stdout.write(self.style.ERROR(f'  ✗ Mensajes: {django_messages} vs {hps_messages}'))
                
                if hps_metrics == django_metrics:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Métricas: {django_metrics}/{hps_metrics}'))
                else:
                    validation_warnings.append(f'Métricas: {django_metrics} en Django vs {hps_metrics} en HPS')
                    self.stdout.write(self.style.WARNING(f'  ⚠ Métricas: {django_metrics} vs {hps_metrics}'))
            except Exception as e:
                validation_warnings.append(f'Chat: Error verificando - {str(e)}')
                self.stdout.write(self.style.WARNING(f'  ⚠ Chat: Error - {str(e)}'))

            # ===== Validar Integridad Referencial =====
            self.stdout.write('\n🔗 Validando Integridad Referencial...')
            
            # Usuarios sin perfil HPS (deberían tenerlo si vienen de HPS)
            users_without_profile = User.objects.filter(hps_profile__isnull=True).exclude(
                id__in=HpsUserMapping.objects.values_list('django_user_id', flat=True)
            ).count()
            if users_without_profile > 0:
                validation_warnings.append(f'{users_without_profile} usuarios Django sin perfil HPS (puede ser normal si no vienen de HPS)')
                self.stdout.write(self.style.WARNING(f'  ⚠ {users_without_profile} usuarios sin perfil HPS'))
            
            # Solicitudes con usuarios no migrados
            requests_without_user = HpsRequest.objects.filter(
                user__hps_mapping__isnull=True
            ).count()
            if requests_without_user > 0:
                validation_errors.append(f'{requests_without_user} solicitudes con usuarios no migrados')
                self.stdout.write(self.style.ERROR(f'  ✗ {requests_without_user} solicitudes con usuarios no migrados'))
            
            # Mensajes con conversaciones no migradas
            messages_without_conv = ChatMessage.objects.filter(
                conversation__isnull=True
            ).count()
            if messages_without_conv > 0:
                validation_errors.append(f'{messages_without_conv} mensajes con conversaciones no migradas')
                self.stdout.write(self.style.ERROR(f'  ✗ {messages_without_conv} mensajes con conversaciones no migradas'))

            # ===== Resumen =====
            self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
            if not validation_errors and not validation_warnings:
                self.stdout.write(self.style.SUCCESS('✅ VALIDACIÓN EXITOSA: Todos los datos migrados correctamente'))
            else:
                if validation_errors:
                    self.stdout.write(self.style.ERROR(f'❌ ERRORES ENCONTRADOS: {len(validation_errors)}'))
                    for error in validation_errors:
                        self.stdout.write(self.style.ERROR(f'  - {error}'))
                if validation_warnings:
                    self.stdout.write(self.style.WARNING(f'⚠ ADVERTENCIAS: {len(validation_warnings)}'))
                    for warning in validation_warnings:
                        self.stdout.write(self.style.WARNING(f'  - {warning}'))
            self.stdout.write(self.style.SUCCESS('=' * 60))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError durante validación: {str(e)}'))
            logger.exception("Error en validación")
            raise
        finally:
            hps_cursor.close()
            hps_conn.close()
            self.stdout.write('\nConexión cerrada')

