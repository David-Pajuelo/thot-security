"""
Management command para actualizar el campo total_messages en todas las conversaciones
"""
from django.core.management.base import BaseCommand
from hps_core.models import ChatConversation


class Command(BaseCommand):
    help = 'Actualiza el campo total_messages en todas las conversaciones basándose en el conteo real de mensajes'

    def handle(self, *args, **options):
        self.stdout.write('🔄 Actualizando contadores de mensajes en conversaciones...')
        
        updated = 0
        total = ChatConversation.objects.count()
        
        for conv in ChatConversation.objects.all():
            old_count = conv.total_messages
            real_count = conv.messages.count()
            
            if old_count != real_count:
                conv.total_messages = real_count
                conv.save(update_fields=['total_messages'])
                updated += 1
                self.stdout.write(f'  ✅ {conv.id}: {old_count} → {real_count} mensajes')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Actualizadas {updated} de {total} conversaciones'))

