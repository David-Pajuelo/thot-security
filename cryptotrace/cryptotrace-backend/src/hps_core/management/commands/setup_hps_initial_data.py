"""
Script para crear datos iniciales de HPS directamente en Django.

Crea roles, equipos y usuarios iniciales para el sistema HPS.
Útil cuando la base de datos está vacía y no hay datos de hps-system para migrar.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from hps_core.models import HpsRole, HpsTeam, HpsUserProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea datos iniciales de HPS (roles, equipos, usuarios)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Eliminar datos existentes antes de crear'
        )

    def handle(self, *args, **options):
        reset = options['reset']

        if reset:
            self.stdout.write(self.style.WARNING('⚠ Eliminando datos existentes...'))
            HpsUserProfile.objects.all().delete()
            HpsTeam.objects.all().delete()
            HpsRole.objects.all().delete()
            User.objects.filter(email__contains='@hps.').delete()
            self.stdout.write(self.style.SUCCESS('✓ Datos eliminados'))

        self.stdout.write(self.style.SUCCESS('\n🚀 Creando datos iniciales de HPS...\n'))

        # ===== CREAR ROLES =====
        self.stdout.write('📋 Creando roles...')
        roles_data = [
            {
                'name': 'admin',
                'description': 'Administrador del sistema HPS',
                'permissions': {
                    'manage_users': True,
                    'manage_teams': True,
                    'approve_hps': True,
                    'view_all_hps': True,
                    'manage_templates': True,
                }
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
                'name': 'team_lead',
                'description': 'Líder de equipo',
                'permissions': {
                    'view_team_hps': True,
                    'submit_hps': True,
                }
            },
            {
                'name': 'member',
                'description': 'Miembro estándar',
                'permissions': {
                    'view_own_hps': True,
                    'submit_hps': True,
                }
            },
        ]

        created_roles = 0
        for role_data in roles_data:
            role, created = HpsRole.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'description': role_data['description'],
                    'permissions': role_data['permissions']
                }
            )
            if created:
                created_roles += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Rol creado: {role.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  ⊙ Rol ya existe: {role.name}'))

        self.stdout.write(f'\nRoles: {created_roles} creados, {len(roles_data) - created_roles} ya existían\n')

        # ===== CREAR EQUIPOS =====
        self.stdout.write('👥 Creando equipos...')
        teams_data = [
            {
                'name': 'Equipo Principal',
                'description': 'Equipo principal de seguridad',
            },
            {
                'name': 'Equipo Soporte',
                'description': 'Equipo de soporte técnico',
            },
        ]

        created_teams = 0
        teams = []
        for team_data in teams_data:
            team, created = HpsTeam.objects.get_or_create(
                name=team_data['name'],
                defaults={
                    'description': team_data['description'],
                    'is_active': True,
                }
            )
            teams.append(team)
            if created:
                created_teams += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Equipo creado: {team.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  ⊙ Equipo ya existe: {team.name}'))

        self.stdout.write(f'\nEquipos: {created_teams} creados, {len(teams_data) - created_teams} ya existían\n')

        # ===== CREAR USUARIOS =====
        self.stdout.write('👤 Creando usuarios...')
        
        # Obtener roles
        admin_role = HpsRole.objects.get(name='admin')
        jefe_role = HpsRole.objects.get(name='jefe_seguridad')
        team_lead_role = HpsRole.objects.get(name='team_lead')
        user_role = HpsRole.objects.get(name='member')

        users_data = [
            {
                'email': 'admin@hps-system.com',
                'password': 'admin123',
                'first_name': 'Admin',
                'last_name': 'HPS',
                'role': admin_role,
                'team': teams[0] if teams else None,
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'email': 'jefe@hps.local',
                'password': 'jefe123',
                'first_name': 'Jefe',
                'last_name': 'Seguridad',
                'role': jefe_role,
                'team': teams[0] if teams else None,
                'is_staff': True,
                'is_superuser': False,
            },
            {
                'email': 'lider@hps.local',
                'password': 'lider123',
                'first_name': 'Líder',
                'last_name': 'Equipo',
                'role': team_lead_role,
                'team': teams[0] if teams else None,
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'email': 'usuario@hps.local',
                'password': 'user123',
                'first_name': 'Usuario',
                'last_name': 'Estándar',
                'role': user_role,
                'team': teams[1] if len(teams) > 1 else None,
                'is_staff': False,
                'is_superuser': False,
            },
        ]

        created_users = 0
        for user_data in users_data:
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

            if user_created:
                user.set_password(user_data['password'])
                user.save()
                created_users += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Usuario creado: {user.email}'))
            else:
                # Actualizar contraseña si existe
                user.set_password(user_data['password'])
                user.is_active = True
                user.is_staff = user_data['is_staff']
                user.is_superuser = user_data['is_superuser']
                user.save()
                self.stdout.write(self.style.WARNING(f'  ⊙ Usuario ya existe, contraseña actualizada: {user.email}'))

            # Crear o actualizar perfil HPS
            profile, profile_created = HpsUserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'role': user_data['role'],
                    'team': user_data['team'],
                    'email_verified': True,
                    'is_temp_password': False,
                    'must_change_password': False,
                }
            )

            if not profile_created:
                profile.role = user_data['role']
                profile.team = user_data['team']
                profile.save()

        # Asignar team_lead al primer equipo
        if teams:
            admin_user = User.objects.get(email='admin@hps-system.com')
            teams[0].team_lead = admin_user
            teams[0].save()
            self.stdout.write(self.style.SUCCESS(f'  ✓ Team lead asignado: {teams[0].name} → {admin_user.email}'))

        self.stdout.write(f'\nUsuarios: {created_users} creados\n')

        # ===== RESUMEN =====
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('✅ Datos iniciales creados'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('\n📋 Credenciales de acceso:\n')
        for user_data in users_data:
            self.stdout.write(f'  Email: {user_data["email"]}')
            self.stdout.write(f'  Contraseña: {user_data["password"]}')
            self.stdout.write(f'  Rol: {user_data["role"].name}')
            self.stdout.write('')

