"""
Comando para crear roles y usuarios basados en el código del sistema.

Crea todos los roles necesarios y un usuario de cada tipo (excepto admin que ya existe).
Todas las contraseñas serán "Password123" y no serán temporales.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from hps_core.models import HpsRole, HpsUserProfile, HpsTeam

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea roles y usuarios basados en el código del sistema (no consulta BD)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            default='Password123',
            help='Contraseña a usar para todos los usuarios (default: Password123)'
        )

    def handle(self, *args, **options):
        password = options['password']

        self.stdout.write(self.style.SUCCESS('\n🚀 Creando roles y usuarios desde el código...\n'))

        # ===== CREAR ROLES (basados en el código) =====
        self.stdout.write('📋 Creando roles...')
        roles_data = [
            {
                'name': 'admin',
                'description': 'Rol admin del sistema HPS',
                'permissions': {}
            },
            {
                'name': 'jefe_seguridad',
                'description': 'Jefe de seguridad',
                'permissions': {
                    'approve_hps': True,
                    'view_all_hps': True,
                    'manage_templates': True,
                }
            },
            {
                'name': 'jefe_seguridad_suplente',
                'description': 'Jefe de seguridad suplente',
                'permissions': {
                    'approve_hps': True,
                    'view_all_hps': True,
                }
            },
            {
                'name': 'crypto',
                'description': 'Perfil base para usuarios de CryptoTrace',
                'permissions': {}
            },
            {
                'name': 'team_lead',
                'description': 'Líder de equipo',
                'permissions': {
                    'submit_hps': True,
                    'view_team_hps': True,
                }
            },
            {
                'name': 'member',
                'description': 'Usuario estándar',
                'permissions': {
                    'submit_hps': True,
                    'view_own_hps': True,
                }
            },
        ]

        created_roles = 0
        roles_dict = {}
        for role_data in roles_data:
            role, created = HpsRole.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'description': role_data['description'],
                    'permissions': role_data['permissions']
                }
            )
            roles_dict[role_data['name']] = role
            if created:
                created_roles += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Rol creado: {role.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  ⊙ Rol ya existe: {role.name}'))

        self.stdout.write(f'\nRoles: {created_roles} creados, {len(roles_data) - created_roles} ya existían\n')

        # ===== CREAR EQUIPO AICOX =====
        self.stdout.write('👥 Creando equipo AICOX...')
        aicox_team, team_created = HpsTeam.objects.get_or_create(
            name='AICOX',
            defaults={
                'description': 'Equipo genérico AICOX',
                'is_active': True,
            }
        )
        if team_created:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Equipo creado: {aicox_team.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'  ⊙ Equipo ya existe: {aicox_team.name}'))
        self.stdout.write('')

        # ===== VERIFICAR SI EXISTE ADMIN =====
        admin_exists = False
        admin_user = User.objects.filter(email='admin@hps-system.com').first()
        if admin_user:
            admin_exists = True
            self.stdout.write(self.style.WARNING('⚠ Usuario admin ya existe, se omitirá la creación\n'))

        # ===== CREAR USUARIOS =====
        self.stdout.write('👤 Creando usuarios...\n')

        # Definir usuarios a crear (todos excepto admin)
        users_to_create = [
            {
                'email': 'jefeseguridad@hps-system.com',
                'first_name': 'Jefe',
                'last_name': 'Seguridad',
                'role_name': 'jefe_seguridad',
                'is_staff': True,
                'is_superuser': False,
            },
            {
                'email': 'jefeseguridadsuplente@hps-system.com',
                'first_name': 'Jefe',
                'last_name': 'Seguridad Suplente',
                'role_name': 'jefe_seguridad_suplente',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'email': 'crypto@hps-system.com',
                'first_name': 'Crypto',
                'last_name': 'Usuario',
                'role_name': 'crypto',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'email': 'teamlead@hps-system.com',
                'first_name': 'Team',
                'last_name': 'Lead',
                'role_name': 'team_lead',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'email': 'member@hps-system.com',
                'first_name': 'Member',
                'last_name': 'Usuario',
                'role_name': 'member',
                'is_staff': False,
                'is_superuser': False,
            },
        ]

        # Si admin no existe, agregarlo a la lista
        if not admin_exists:
            users_to_create.insert(0, {
                'email': 'admin@hps-system.com',
                'first_name': 'Admin',
                'last_name': 'HPS',
                'role_name': 'admin',
                'is_staff': True,
                'is_superuser': True,
            })

        created_count = 0
        updated_count = 0

        for user_data in users_to_create:
            role = roles_dict[user_data['role_name']]
            
            # Crear o actualizar usuario
            user, user_created = User.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'username': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'is_active': True,
                    'is_staff': user_data['is_staff'],
                    'is_superuser': user_data['is_superuser'],
                }
            )

            if not user_created:
                # Actualizar datos del usuario existente
                user.first_name = user_data['first_name']
                user.last_name = user_data['last_name']
                user.is_active = True
                user.is_staff = user_data['is_staff']
                user.is_superuser = user_data['is_superuser']
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
                    'team': aicox_team,
                    'email_verified': True,
                    'is_temp_password': False,
                    'must_change_password': False,
                }
            )

            if not profile_created:
                # Actualizar perfil existente
                profile.role = role
                profile.team = aicox_team
                profile.email_verified = True
                profile.is_temp_password = False
                profile.must_change_password = False
                profile.save()

            if user_created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Usuario creado: {user.email} ({role.name})'))
            else:
                self.stdout.write(self.style.WARNING(f'  ↻ Usuario actualizado: {user.email} ({role.name})'))

        # ===== RESUMEN =====
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('✅ Proceso completado'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'\n📊 Resumen:')
        self.stdout.write(f'  • Roles creados: {created_roles}')
        self.stdout.write(f'  • Usuarios creados: {created_count}')
        self.stdout.write(f'  • Usuarios actualizados: {updated_count}')
        self.stdout.write(f'\n🔑 Contraseña para todos los usuarios: {password}')
        self.stdout.write(f'\n📋 Usuarios creados/actualizados:\n')
        
        for user_data in users_to_create:
            self.stdout.write(f'  • {user_data["email"]} - {user_data["role_name"]}')
