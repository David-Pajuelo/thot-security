"""
Comando para crear usuarios basados en los roles existentes en la base de datos.

Lee los roles existentes y crea un usuario de cada tipo (excepto admin que ya existe).
Todas las contraseñas serán "Password123" y no serán temporales.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from hps_core.models import HpsRole, HpsUserProfile, HpsTeam

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea usuarios basados en los roles existentes en la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            default='Password123',
            help='Contraseña a usar para todos los usuarios (default: Password123)'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='No actualizar usuarios que ya existen'
        )

    def handle(self, *args, **options):
        password = options['password']
        skip_existing = options['skip_existing']

        self.stdout.write(self.style.SUCCESS('\n🔍 Consultando roles existentes en la base de datos...\n'))

        # Obtener todos los roles existentes
        existing_roles = HpsRole.objects.all().order_by('name')
        
        if not existing_roles.exists():
            self.stdout.write(self.style.ERROR('❌ No se encontraron roles en la base de datos.'))
            self.stdout.write(self.style.WARNING('   Ejecuta primero: python manage.py setup_hps_initial_data'))
            return

        self.stdout.write(f'📋 Roles encontrados: {existing_roles.count()}\n')
        for role in existing_roles:
            self.stdout.write(f'  • {role.name}: {role.description or "Sin descripción"}')

        # Obtener o crear un equipo por defecto
        default_team, _ = HpsTeam.objects.get_or_create(
            name='AICOX',
            defaults={
                'description': 'Equipo genérico para usuarios sin equipo específico',
                'is_active': True,
            }
        )

        # Verificar si existe usuario admin
        admin_exists = False
        admin_role = existing_roles.filter(name='admin').first()
        if admin_role:
            admin_profiles = HpsUserProfile.objects.filter(role=admin_role)
            if admin_profiles.exists():
                admin_exists = True
                self.stdout.write(f'\n✓ Usuario admin ya existe, se omitirá la creación de usuario admin\n')

        self.stdout.write(self.style.SUCCESS('\n👤 Creando usuarios...\n'))

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for role in existing_roles:
            # Saltar admin si ya existe
            if role.name == 'admin' and admin_exists:
                self.stdout.write(self.style.WARNING(f'  ⊙ Saltando {role.name} (usuario admin ya existe)'))
                skipped_count += 1
                continue

            # Generar email basado en el nombre del rol
            role_name_clean = role.name.lower().replace('_', '')
            email = f'{role_name_clean}@hps-system.com'
            
            # Si el email es muy largo o tiene caracteres especiales, usar formato más simple
            if len(email) > 50 or '@' not in email:
                email = f'user_{role.name.lower()}@hps-system.com'

            # Verificar si el usuario ya existe
            user_exists = User.objects.filter(email=email).exists()
            
            if user_exists and skip_existing:
                self.stdout.write(self.style.WARNING(f'  ⊙ Usuario ya existe (saltado): {email} ({role.name})'))
                skipped_count += 1
                continue

            # Crear o actualizar usuario
            user, user_created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': role.name.replace('_', ' ').title(),
                    'last_name': 'Usuario',
                    'is_active': True,
                    'is_staff': role.name == 'admin',
                    'is_superuser': role.name == 'admin',
                }
            )

            if not user_created:
                # Actualizar datos del usuario existente
                user.first_name = role.name.replace('_', ' ').title()
                user.last_name = 'Usuario'
                user.is_active = True
                user.is_staff = role.name == 'admin'
                user.is_superuser = role.name == 'admin'
                updated_count += 1
            else:
                created_count += 1

            # Establecer contraseña
            user.set_password(password)
            user.save()

            # Crear o actualizar perfil HPS
            profile, profile_created = HpsUserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'role': role,
                    'team': default_team,
                    'email_verified': True,
                    'is_temp_password': False,
                    'must_change_password': False,
                }
            )

            if not profile_created:
                # Actualizar perfil existente
                profile.role = role
                profile.team = default_team
                profile.email_verified = True
                profile.is_temp_password = False
                profile.must_change_password = False
                profile.save()

            if user_created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Usuario creado: {email} ({role.name})'))
            else:
                self.stdout.write(self.style.WARNING(f'  ↻ Usuario actualizado: {email} ({role.name})'))

        # ===== RESUMEN =====
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('✅ Proceso completado'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'\n📊 Resumen:')
        self.stdout.write(f'  • Usuarios creados: {created_count}')
        self.stdout.write(f'  • Usuarios actualizados: {updated_count}')
        self.stdout.write(f'  • Usuarios saltados: {skipped_count}')
        self.stdout.write(f'\n🔑 Contraseña para todos los usuarios: {password}')
        self.stdout.write(f'\n📋 Usuarios creados/actualizados:\n')
        
        # Mostrar lista de usuarios
        for role in existing_roles:
            if role.name == 'admin' and admin_exists:
                continue
            role_name_clean = role.name.lower().replace('_', '')
            email = f'{role_name_clean}@hps-system.com'
            if len(email) > 50 or '@' not in email:
                email = f'user_{role.name.lower()}@hps-system.com'
            
            user = User.objects.filter(email=email).first()
            if user:
                self.stdout.write(f'  • {email} - {role.name}')

