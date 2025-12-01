"""
Comando de gestión para actualizar usernames de usuarios HPS para que coincidan con su email.
Esto permite que el login funcione correctamente con el email como username.
"""
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Actualiza los usernames de usuarios para que coincidan con su email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular la actualización sin hacer cambios reales',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar actualización incluso si el username ya es el email',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('ACTUALIZACIÓN DE USERNAMES A EMAIL'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  MODO DRY-RUN: No se realizarán cambios reales'))
        
        # Obtener todos los usuarios que tienen email
        users = User.objects.exclude(email='').exclude(email__isnull=True)
        
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for user in users:
            current_username = user.username
            email = user.email
            
            # Si el username ya es el email y no se fuerza, saltar
            if current_username == email and not force:
                skipped_count += 1
                continue
            
            # Verificar si ya existe otro usuario con ese email como username
            existing_user = User.objects.filter(username=email).exclude(id=user.id).first()
            if existing_user:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Usuario {user.id} ({user.email}): '
                        f'Ya existe otro usuario con username="{email}" (ID: {existing_user.id})'
                    )
                )
                error_count += 1
                continue
            
            # Actualizar username
            if not dry_run:
                try:
                    with transaction.atomic():
                        user.username = email
                        user.save(update_fields=['username'])
                        logger.info(f"Username actualizado: {current_username} -> {email} (Usuario ID: {user.id})")
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ Error actualizando usuario {user.id} ({user.email}): {str(e)}'
                        )
                    )
                    error_count += 1
                    continue
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Usuario {user.id} ({user.email}): '
                    f'username="{current_username}" -> "{email}"'
                )
            )
            updated_count += 1
        
        # Resumen
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('RESUMEN:'))
        self.stdout.write(self.style.SUCCESS(f'  ✓ Actualizados: {updated_count}'))
        self.stdout.write(self.style.SUCCESS(f'  ⊘ Omitidos: {skipped_count}'))
        self.stdout.write(self.style.SUCCESS(f'  ❌ Errores: {error_count}'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  Este fue un DRY-RUN. Para aplicar los cambios, ejecuta sin --dry-run'
                )
            )

