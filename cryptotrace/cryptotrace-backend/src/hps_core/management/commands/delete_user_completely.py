"""
Comando de Django para eliminar completamente un usuario de la base de datos
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from hps_core.models import HpsUserProfile, HpsRequest, ChatConversation, ChatMessage
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Eliminar completamente un usuario de la base de datos (hard delete)'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email del usuario a eliminar')
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar eliminación sin confirmación',
        )

    def handle(self, *args, **options):
        email = options['email']
        force = options.get('force', False)
        
        try:
            # Buscar usuario
            user = User.objects.filter(email=email).first()
            
            if not user:
                self.stdout.write(self.style.ERROR(f'❌ Usuario con email {email} no encontrado'))
                return
            
            self.stdout.write(self.style.WARNING(f'\n⚠️  Usuario encontrado: {email}'))
            self.stdout.write(f'  ID: {user.id}')
            self.stdout.write(f'  Username: {user.username}')
            self.stdout.write(f'  Email: {user.email}')
            self.stdout.write(f'  First Name: {user.first_name}')
            self.stdout.write(f'  Last Name: {user.last_name}')
            self.stdout.write(f'  is_active: {user.is_active}')
            
            # Verificar relaciones
            has_profile = hasattr(user, 'hps_profile')
            hps_requests_count = user.hps_requests.count() if hasattr(user, 'hps_requests') else 0
            chat_conversations_count = user.chat_conversations.count() if hasattr(user, 'chat_conversations') else 0
            
            self.stdout.write(f'\n📋 Relaciones:')
            self.stdout.write(f'  Perfil HPS: {"Sí" if has_profile else "No"}')
            self.stdout.write(f'  HPS Requests: {hps_requests_count}')
            self.stdout.write(f'  Chat Conversations: {chat_conversations_count}')
            
            if not force:
                confirm = input('\n¿Estás seguro de que quieres eliminar completamente este usuario? (escribe "SI" para confirmar): ')
                if confirm != "SI":
                    self.stdout.write(self.style.WARNING('❌ Operación cancelada'))
                    return
            
            # Eliminar en cascada (el orden importa debido a las foreign keys)
            deleted_items = {}
            
            # 1. Eliminar mensajes de chat
            if hasattr(user, 'chat_conversations'):
                messages_count = ChatMessage.objects.filter(conversation__user=user).count()
                ChatMessage.objects.filter(conversation__user=user).delete()
                deleted_items['chat_messages'] = messages_count
            
            # 2. Eliminar conversaciones de chat
            if hasattr(user, 'chat_conversations'):
                conversations_count = user.chat_conversations.count()
                user.chat_conversations.all().delete()
                deleted_items['chat_conversations'] = conversations_count
            
            # 3. Eliminar solicitudes HPS relacionadas
            if hasattr(user, 'hps_requests'):
                hps_requests = user.hps_requests.all()
                hps_count = hps_requests.count()
                hps_requests.delete()
                deleted_items['hps_requests'] = hps_count
            
            # 4. Eliminar perfil HPS (esto eliminará el usuario por CASCADE si está configurado)
            if has_profile:
                profile = user.hps_profile
                profile.delete()
                deleted_items['hps_profile'] = 1
            
            # 5. Eliminar usuario
            user_id = user.id
            user_email = user.email
            user.delete()
            deleted_items['user'] = 1
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ Usuario {user_email} eliminado completamente'))
            self.stdout.write(f'\n📊 Resumen de eliminación:')
            for item, count in deleted_items.items():
                self.stdout.write(f'  • {item}: {count}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())

