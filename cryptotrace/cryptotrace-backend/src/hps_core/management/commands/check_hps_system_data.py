"""
Script para verificar qué datos existen en la base de datos de hps-system.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Verifica qué datos existen en la base de datos de hps-system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hps-db-url',
            type=str,
            help='URL de conexión a base HPS: postgresql://user:pass@host:port/dbname. Si no se proporciona, intenta usar variables de entorno.'
        )

    def handle(self, *args, **options):
        hps_db_url = options.get('hps_db_url')
        
        if not hps_db_url:
            # Intentar construir desde variables de entorno comunes
            import os
            db_host = os.getenv('HPS_POSTGRES_HOST', 'localhost')
            db_port = os.getenv('HPS_POSTGRES_PORT', '5432')
            db_name = os.getenv('HPS_POSTGRES_DB', 'hps_db')
            db_user = os.getenv('HPS_POSTGRES_USER', 'postgres')
            db_password = os.getenv('HPS_POSTGRES_PASSWORD', 'postgres')
            hps_db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            self.stdout.write(self.style.WARNING(f'Usando URL construida: postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}'))

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('VERIFICACIÓN DE DATOS EN HPS-SYSTEM'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # Conectar a base HPS
        try:
            hps_conn = psycopg2.connect(hps_db_url)
            hps_cursor = hps_conn.cursor(cursor_factory=RealDictCursor)
            self.stdout.write(self.style.SUCCESS('\n✓ Conectado a base HPS-System\n'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error conectando a base HPS: {str(e)}'))
            self.stdout.write(self.style.WARNING('\n💡 Sugerencia: Proporciona --hps-db-url o configura las variables de entorno:'))
            self.stdout.write('   HPS_POSTGRES_HOST, HPS_POSTGRES_PORT, HPS_POSTGRES_DB, HPS_POSTGRES_USER, HPS_POSTGRES_PASSWORD')
            return

        try:
            # Verificar tablas existentes
            hps_cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            tables = [row['table_name'] for row in hps_cursor.fetchall()]
            self.stdout.write(f'📋 Tablas encontradas: {len(tables)}')
            for table in tables:
                self.stdout.write(f'   - {table}')

            # Roles
            try:
                hps_cursor.execute("SELECT COUNT(*) as count FROM roles")
                roles_count = hps_cursor.fetchone()['count']
                self.stdout.write(f'\n📋 Roles: {roles_count}')
                if roles_count > 0:
                    hps_cursor.execute("SELECT name FROM roles ORDER BY name LIMIT 10")
                    for role in hps_cursor.fetchall():
                        self.stdout.write(f'   - {role["name"]}')
            except Exception as e:
                self.stdout.write(f'\n📋 Roles: (tabla no existe o error: {str(e)})')

            # Usuarios
            try:
                hps_cursor.execute("SELECT COUNT(*) as count FROM users")
                users_count = hps_cursor.fetchone()['count']
                self.stdout.write(f'\n👤 Usuarios: {users_count}')
                if users_count > 0:
                    hps_cursor.execute("SELECT email, first_name, last_name, is_active FROM users ORDER BY created_at LIMIT 10")
                    for user in hps_cursor.fetchall():
                        status = "activo" if user['is_active'] else "inactivo"
                        self.stdout.write(f'   - {user["email"]} ({user["first_name"]} {user["last_name"]}) - {status}')
            except Exception as e:
                self.stdout.write(f'\n👤 Usuarios: (tabla no existe o error: {str(e)})')

            # Equipos
            try:
                hps_cursor.execute("SELECT COUNT(*) as count FROM teams")
                teams_count = hps_cursor.fetchone()['count']
                self.stdout.write(f'\n👥 Equipos: {teams_count}')
                if teams_count > 0:
                    hps_cursor.execute("SELECT name, is_active FROM teams ORDER BY name LIMIT 10")
                    for team in hps_cursor.fetchall():
                        status = "activo" if team['is_active'] else "inactivo"
                        self.stdout.write(f'   - {team["name"]} - {status}')
            except Exception as e:
                self.stdout.write(f'\n👥 Equipos: (tabla no existe o error: {str(e)})')

            # Plantillas
            try:
                hps_cursor.execute("SELECT COUNT(*) as count FROM hps_templates")
                templates_count = hps_cursor.fetchone()['count']
                self.stdout.write(f'\n📄 Plantillas HPS: {templates_count}')
                if templates_count > 0:
                    hps_cursor.execute("SELECT name, template_type, version, active FROM hps_templates ORDER BY name LIMIT 10")
                    for template in hps_cursor.fetchall():
                        has_pdf = True  # Asumimos que tienen PDF si existen
                        self.stdout.write(f'   - {template["name"]} v{template["version"]} ({template["template_type"]})')
            except Exception as e:
                self.stdout.write(f'\n📄 Plantillas: (tabla no existe o error: {str(e)})')

            # Solicitudes HPS
            try:
                hps_cursor.execute("SELECT COUNT(*) as count FROM hps_requests")
                requests_count = hps_cursor.fetchone()['count']
                self.stdout.write(f'\n📝 Solicitudes HPS: {requests_count}')
                if requests_count > 0:
                    # Estadísticas por estado
                    hps_cursor.execute("""
                        SELECT status, COUNT(*) as count 
                        FROM hps_requests 
                        GROUP BY status
                    """)
                    for stat in hps_cursor.fetchall():
                        self.stdout.write(f'   - {stat["status"]}: {stat["count"]}')
                    # Con PDFs
                    hps_cursor.execute("SELECT COUNT(*) as count FROM hps_requests WHERE filled_pdf IS NOT NULL")
                    with_filled = hps_cursor.fetchone()['count']
                    hps_cursor.execute("SELECT COUNT(*) as count FROM hps_requests WHERE response_pdf IS NOT NULL")
                    with_response = hps_cursor.fetchone()['count']
                    self.stdout.write(f'   - Con filled_pdf: {with_filled}')
                    self.stdout.write(f'   - Con response_pdf: {with_response}')
            except Exception as e:
                self.stdout.write(f'\n📝 Solicitudes: (tabla no existe o error: {str(e)})')

            # Tokens
            try:
                hps_cursor.execute("SELECT COUNT(*) as count FROM hps_tokens")
                tokens_count = hps_cursor.fetchone()['count']
                self.stdout.write(f'\n🔑 Tokens HPS: {tokens_count}')
                if tokens_count > 0:
                    hps_cursor.execute("SELECT COUNT(*) as count FROM hps_tokens WHERE is_used = true")
                    used = hps_cursor.fetchone()['count']
                    self.stdout.write(f'   - Usados: {used}')
                    self.stdout.write(f'   - No usados: {tokens_count - used}')
            except Exception as e:
                self.stdout.write(f'\n🔑 Tokens: (tabla no existe o error: {str(e)})')

            # Logs de auditoría
            try:
                hps_cursor.execute("SELECT COUNT(*) as count FROM audit_logs")
                audit_count = hps_cursor.fetchone()['count']
                self.stdout.write(f'\n📊 Logs de auditoría: {audit_count}')
            except Exception as e:
                self.stdout.write(f'\n📊 Logs: (tabla no existe o error: {str(e)})')

            # Chat
            try:
                hps_cursor.execute("SELECT COUNT(*) as count FROM chat_conversations")
                conversations_count = hps_cursor.fetchone()['count']
                hps_cursor.execute("SELECT COUNT(*) as count FROM chat_messages")
                messages_count = hps_cursor.fetchone()['count']
                hps_cursor.execute("SELECT COUNT(*) as count FROM chat_metrics")
                metrics_count = hps_cursor.fetchone()['count']
                self.stdout.write(f'\n💬 Chat:')
                self.stdout.write(f'   - Conversaciones: {conversations_count}')
                self.stdout.write(f'   - Mensajes: {messages_count}')
                self.stdout.write(f'   - Métricas: {metrics_count}')
            except Exception as e:
                self.stdout.write(f'\n💬 Chat: (tablas no existen o error: {str(e)})')

            self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
            self.stdout.write(self.style.SUCCESS('Verificación completada'))
            self.stdout.write(self.style.SUCCESS('=' * 60))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError durante verificación: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
        finally:
            hps_cursor.close()
            hps_conn.close()
            self.stdout.write('\nConexión cerrada')

