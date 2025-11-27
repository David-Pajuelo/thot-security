"""
Script para crear o resetear usuario admin de HPS.

Crea un usuario admin con perfil HPS o resetea la contraseña de uno existente.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from hps_core.models import HpsRole, HpsUserProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea o resetea usuario admin de HPS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='admin@hps-system.com',
            help='Email del usuario admin (default: admin@hps-system.com)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Contraseña del usuario (default: admin123)'
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Resetear contraseña de usuario existente'
        )
        parser.add_argument(
            '--role',
            type=str,
            default='admin',
            help='Nombre del rol HPS (default: admin)'
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        reset = options['reset']
        role_name = options['role']

        # Obtener o crear rol
        role, created = HpsRole.objects.get_or_create(
            name=role_name,
            defaults={
                'description': f'Rol {role_name} del sistema HPS',
                'permissions': {}
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Rol "{role_name}" creado'))

        # Verificar si usuario existe
        user = User.objects.filter(email=email).first()

        if user:
            if reset:
                # Resetear contraseña
                user.set_password(password)
                user.is_active = True
                user.is_staff = True
                user.is_superuser = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Contraseña reseteada para usuario: {email}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ Usuario ya existe: {email} (usa --reset para resetear contraseña)'))
                return
        else:
            # Crear nuevo usuario
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name='Admin',
                last_name='HPS',
                is_active=True,
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Usuario admin creado: {email}'))

        # Crear o actualizar perfil HPS
        profile, created = HpsUserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': role,
                'email_verified': True,
                'is_temp_password': False,
                'must_change_password': False,
            }
        )
        
        if not created:
            # Actualizar perfil existente
            profile.role = role
            profile.email_verified = True
            profile.is_temp_password = False
            profile.must_change_password = False
            profile.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Perfil HPS actualizado'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Perfil HPS creado'))

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('Credenciales de acceso:'))
        self.stdout.write(self.style.SUCCESS(f'  Email: {email}'))
        self.stdout.write(self.style.SUCCESS(f'  Contraseña: {password}'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

