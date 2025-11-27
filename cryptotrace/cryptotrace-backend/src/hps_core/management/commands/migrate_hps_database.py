"""
Script principal de migración de base de datos HPS-System a CryptoTrace.

Este script orquesta la migración completa de todos los datos de hps-system
a la base de datos de cryptotrace, siguiendo el orden correcto de dependencias.
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migra toda la base de datos de hps-system a cryptotrace'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hps-db-url',
            type=str,
            required=True,
            help='URL de conexión a base HPS: postgresql://user:pass@host:port/dbname'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar sin guardar cambios'
        )
        parser.add_argument(
            '--skip-users',
            action='store_true',
            help='Saltar migración de usuarios'
        )
        parser.add_argument(
            '--skip-chat',
            action='store_true',
            help='Saltar migración de chat'
        )
        parser.add_argument(
            '--skip-pdfs',
            action='store_true',
            help='Saltar migración de PDFs (solo estructura)'
        )

    def handle(self, *args, **options):
        hps_db_url = options['hps_db_url']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('=' * 60))
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se guardarán cambios'))
            self.stdout.write(self.style.WARNING('=' * 60))

        self.stdout.write(self.style.SUCCESS('\n🚀 Iniciando migración de base de datos HPS-System → CryptoTrace\n'))

        # Verificar conexión a base HPS
        try:
            hps_conn = psycopg2.connect(hps_db_url)
            hps_cursor = hps_conn.cursor(cursor_factory=RealDictCursor)
            # Intentar contar roles (puede que la tabla no exista)
            try:
                hps_cursor.execute("SELECT COUNT(*) as count FROM roles")
                roles_count = hps_cursor.fetchone()['count']
                self.stdout.write(self.style.SUCCESS(f'✓ Conectado a base HPS (encontrados {roles_count} roles)'))
            except:
                self.stdout.write(self.style.SUCCESS('✓ Conectado a base HPS'))
            hps_cursor.close()
            hps_conn.close()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error conectando a base HPS: {str(e)}'))
            self.stdout.write(self.style.WARNING('\n💡 Verifica que la base de datos HPS esté accesible y la URL sea correcta'))
            return

        # Ejecutar migraciones en orden
        steps = []

        # FASE 1: Datos sin dependencias
        steps.append(('Roles', 'migrate_hps_roles', not options.get('skip_users')))

        if not options.get('skip_users'):
            # FASE 2: Usuarios y equipos (dependen de roles)
            steps.append(('Equipos', 'migrate_hps_teams', True))
            steps.append(('Usuarios', 'migrate_hps_users', True))
            steps.append(('Actualizar Team Leads', 'update_team_leads', True))

            # FASE 3: Datos que dependen de usuarios
            steps.append(('Plantillas', 'migrate_hps_templates', True))
            steps.append(('Tokens', 'migrate_hps_tokens', True))
            steps.append(('Solicitudes HPS', 'migrate_hps_requests', True))
            steps.append(('Logs de Auditoría', 'migrate_hps_audit_logs', True))

            if not options.get('skip_pdfs'):
                steps.append(('PDFs de Solicitudes', 'migrate_hps_pdfs', True))

            if not options.get('skip_chat'):
                steps.append(('Chat', 'migrate_hps_chat', True))

        # Ejecutar pasos
        for step_name, command_name, should_run in steps:
            if not should_run:
                self.stdout.write(self.style.WARNING(f'\n⏭️  Saltando: {step_name}'))
                continue

            self.stdout.write(self.style.SUCCESS(f'\n📦 Migrando: {step_name}'))
            self.stdout.write('-' * 60)

            try:
                call_command(
                    command_name,
                    hps_db_url=hps_db_url,
                    dry_run=dry_run
                )
                self.stdout.write(self.style.SUCCESS(f'✓ {step_name} completado'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Error en {step_name}: {str(e)}'))
                logger.exception(f"Error en migración de {step_name}")
                if not dry_run:
                    self.stdout.write(self.style.WARNING('¿Continuar con el siguiente paso? (s/n)'))
                    # En producción, esto podría ser interactivo o configurable
                    raise

        # Validación final
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('✅ Migración completada'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if not dry_run:
            self.stdout.write('\n📊 Ejecutando validaciones...')
            try:
                call_command('validate_migration', hps_db_url=hps_db_url)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Validación no disponible: {str(e)}'))

