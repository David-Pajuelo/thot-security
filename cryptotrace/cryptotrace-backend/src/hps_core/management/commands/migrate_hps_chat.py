"""
Script de migración de datos de chat desde hps-system a Django.

Migra:
- Conversaciones de chat (chat_conversations)
- Mensajes de chat (chat_messages)
- Métricas de chat (chat_metrics)

Requiere que los usuarios ya estén migrados para mapear user_id.
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from django.core.management.base import BaseCommand
from django.db import transaction
from hps_core.models import ChatConversation, ChatMessage, ChatMetrics, HpsUserMapping

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migra datos de chat de hps-system a Django'

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

    def handle(self, *args, **options):
        hps_db_url = options['hps_db_url']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se guardarán cambios'))

        # Conectar a base HPS
        try:
            hps_conn = psycopg2.connect(hps_db_url)
            hps_cursor = hps_conn.cursor(cursor_factory=RealDictCursor)
            self.stdout.write(self.style.SUCCESS('✓ Conectado a base HPS'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error conectando a base HPS: {str(e)}'))
            return

        try:
            # ===== FASE 1: Migrar Conversaciones =====
            self.stdout.write(self.style.SUCCESS('\n📦 FASE 1: Migrando conversaciones...'))
            
            hps_cursor.execute("SELECT COUNT(*) as count FROM chat_conversations")
            conversations_total = hps_cursor.fetchone()['count']
            self.stdout.write(f'Encontradas {conversations_total} conversaciones en HPS-System')

            if not dry_run:
                conversations_migrated = 0
                conversations_skipped = 0
                conversations_errors = 0

                # Crear mapeo de conversaciones (UUID HPS → UUID Django)
                conversation_mapping = {}

                with transaction.atomic():
                    hps_cursor.execute("""
                        SELECT 
                            id, user_id, session_id, title, status,
                            total_messages, total_tokens_used, conversation_data,
                            created_at, updated_at, completed_at, closed_at
                        FROM chat_conversations
                        ORDER BY created_at
                    """)
                    
                    for conv_data in hps_cursor.fetchall():
                        try:
                            # Verificar si ya existe
                            existing_conv = ChatConversation.objects.filter(id=conv_data['id']).first()
                            
                            if existing_conv:
                                conversations_skipped += 1
                                conversation_mapping[conv_data['id']] = existing_conv.id
                                continue

                            # Mapear user_id
                            user_mapping = HpsUserMapping.objects.filter(
                                hps_user_uuid=conv_data['user_id']
                            ).first()

                            if not user_mapping:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'  ⚠ Usuario no migrado: user_id={conv_data["user_id"]} para conversación {conv_data["id"]}'
                                    )
                                )
                                conversations_errors += 1
                                continue

                            # Crear conversación en Django
                            django_conv = ChatConversation.objects.create(
                                id=conv_data['id'],  # Preservar UUID
                                user=user_mapping.django_user,
                                session_id=conv_data['session_id'],
                                title=conv_data.get('title') or '',
                                status=conv_data.get('status', 'active'),
                                total_messages=conv_data.get('total_messages', 0),
                                total_tokens_used=conv_data.get('total_tokens_used', 0),
                                conversation_data=conv_data.get('conversation_data'),
                                completed_at=conv_data.get('completed_at'),
                                closed_at=conv_data.get('closed_at'),
                            )

                            conversation_mapping[conv_data['id']] = django_conv.id
                            conversations_migrated += 1
                            
                            if conversations_migrated % 50 == 0:
                                self.stdout.write(f'  ... {conversations_migrated} conversaciones migradas')

                        except Exception as e:
                            conversations_errors += 1
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ Error con conversación {conv_data.get("id", "unknown")}: {str(e)}')
                            )
                            logger.exception(f"Error migrando conversación {conv_data.get('id', 'unknown')}")

                self.stdout.write(self.style.SUCCESS(
                    f'Conversaciones: {conversations_migrated} migradas, {conversations_skipped} saltadas, {conversations_errors} errores'
                ))

            # ===== FASE 2: Migrar Mensajes =====
            self.stdout.write(self.style.SUCCESS('\n📦 FASE 2: Migrando mensajes...'))
            
            hps_cursor.execute("SELECT COUNT(*) as count FROM chat_messages")
            messages_total = hps_cursor.fetchone()['count']
            self.stdout.write(f'Encontrados {messages_total} mensajes en HPS-System')

            if not dry_run:
                messages_migrated = 0
                messages_skipped = 0
                messages_errors = 0

                with transaction.atomic():
                    hps_cursor.execute("""
                        SELECT 
                            id, conversation_id, message_type, content,
                            tokens_used, response_time_ms, is_error,
                            error_message, message_metadata, created_at
                        FROM chat_messages
                        ORDER BY created_at
                    """)
                    
                    for msg_data in hps_cursor.fetchall():
                        try:
                            # Verificar si ya existe
                            existing_msg = ChatMessage.objects.filter(id=msg_data['id']).first()
                            
                            if existing_msg:
                                messages_skipped += 1
                                continue

                            # Verificar que la conversación existe (debe estar en el mapeo o en Django)
                            conversation_id = conversation_mapping.get(msg_data['conversation_id'])
                            if not conversation_id:
                                # Intentar buscar directamente
                                django_conv = ChatConversation.objects.filter(id=msg_data['conversation_id']).first()
                                if not django_conv:
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f'  ⚠ Conversación no encontrada: {msg_data["conversation_id"]} para mensaje {msg_data["id"]}'
                                        )
                                    )
                                    messages_errors += 1
                                    continue
                                conversation_id = django_conv.id

                            # Crear mensaje en Django
                            ChatMessage.objects.create(
                                id=msg_data['id'],  # Preservar UUID
                                conversation_id=conversation_id,
                                message_type=msg_data['message_type'],
                                content=msg_data['content'],
                                tokens_used=msg_data.get('tokens_used', 0),
                                response_time_ms=msg_data.get('response_time_ms'),
                                is_error=msg_data.get('is_error', False),
                                error_message=msg_data.get('error_message') or '',
                                message_metadata=msg_data.get('message_metadata') or '',
                            )

                            messages_migrated += 1
                            
                            if messages_migrated % 100 == 0:
                                self.stdout.write(f'  ... {messages_migrated} mensajes migrados')

                        except Exception as e:
                            messages_errors += 1
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ Error con mensaje {msg_data.get("id", "unknown")}: {str(e)}')
                            )
                            logger.exception(f"Error migrando mensaje {msg_data.get('id', 'unknown')}")

                self.stdout.write(self.style.SUCCESS(
                    f'Mensajes: {messages_migrated} migrados, {messages_skipped} saltados, {messages_errors} errores'
                ))

            # ===== FASE 3: Migrar Métricas =====
            self.stdout.write(self.style.SUCCESS('\n📦 FASE 3: Migrando métricas...'))
            
            hps_cursor.execute("SELECT COUNT(*) as count FROM chat_metrics")
            metrics_total = hps_cursor.fetchone()['count']
            self.stdout.write(f'Encontradas {metrics_total} métricas en HPS-System')

            if not dry_run:
                metrics_migrated = 0
                metrics_skipped = 0
                metrics_errors = 0

                with transaction.atomic():
                    hps_cursor.execute("""
                        SELECT 
                            id, date, total_conversations, total_messages,
                            total_tokens_used, avg_response_time_ms, avg_satisfaction_rating,
                            error_rate, active_users, peak_concurrent_users,
                            most_common_topics, system_health_score, created_at
                        FROM chat_metrics
                        ORDER BY date
                    """)
                    
                    for metric_data in hps_cursor.fetchall():
                        try:
                            # Verificar si ya existe
                            existing_metric = ChatMetrics.objects.filter(id=metric_data['id']).first()
                            
                            if existing_metric:
                                metrics_skipped += 1
                                continue

                            # Crear métrica en Django
                            ChatMetrics.objects.create(
                                id=metric_data['id'],  # Preservar UUID
                                date=metric_data['date'],
                                total_conversations=metric_data.get('total_conversations', 0),
                                total_messages=metric_data.get('total_messages', 0),
                                total_tokens_used=metric_data.get('total_tokens_used', 0),
                                avg_response_time_ms=metric_data.get('avg_response_time_ms', 0.0),
                                avg_satisfaction_rating=metric_data.get('avg_satisfaction_rating', 0.0),
                                error_rate=metric_data.get('error_rate', 0.0),
                                active_users=metric_data.get('active_users', 0),
                                peak_concurrent_users=metric_data.get('peak_concurrent_users', 0),
                                most_common_topics=metric_data.get('most_common_topics') or '',
                                system_health_score=metric_data.get('system_health_score', 100.0),
                            )

                            metrics_migrated += 1

                        except Exception as e:
                            metrics_errors += 1
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ Error con métrica {metric_data.get("id", "unknown")}: {str(e)}')
                            )
                            logger.exception(f"Error migrando métrica {metric_data.get('id', 'unknown')}")

                self.stdout.write(self.style.SUCCESS(
                    f'Métricas: {metrics_migrated} migradas, {metrics_skipped} saltadas, {metrics_errors} errores'
                ))

            self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
            self.stdout.write(self.style.SUCCESS('Migración de chat completada'))
            self.stdout.write(self.style.SUCCESS('=' * 60))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error en migración: {str(e)}'))
            logger.exception("Error en migración de chat")
            raise
        finally:
            hps_cursor.close()
            hps_conn.close()
            self.stdout.write('Conexión cerrada')

