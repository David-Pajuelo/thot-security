"""
Comando de Django para analizar los datos de un usuario en la base de datos
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from hps_core.models import HpsUserProfile, HpsRole, HpsTeam
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Analizar datos de un usuario en la base de datos'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email del usuario a analizar')

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            # Buscar usuario
            user = User.objects.filter(email=email).first()
            
            if not user:
                self.stdout.write(self.style.ERROR(f'❌ Usuario con email {email} no encontrado'))
                return
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ Usuario encontrado: {email}\n'))
            self.stdout.write('=' * 80)
            
            # Datos del User (Django)
            self.stdout.write(self.style.WARNING('\n📋 DATOS DEL MODELO USER (Django):'))
            self.stdout.write(f'  ID: {user.id}')
            self.stdout.write(f'  Username: {user.username}')
            self.stdout.write(f'  Email: {user.email}')
            self.stdout.write(f'  First Name: {user.first_name}')
            self.stdout.write(f'  Last Name: {user.last_name}')
            self.stdout.write(f'  is_active: {user.is_active}')
            self.stdout.write(f'  is_staff: {user.is_staff}')
            self.stdout.write(f'  is_superuser: {user.is_superuser}')
            self.stdout.write(f'  date_joined: {user.date_joined}')
            self.stdout.write(f'  last_login: {user.last_login}')
            
            # Verificar si tiene perfil HPS
            has_hps_profile = hasattr(user, 'hps_profile')
            self.stdout.write(f'  Tiene perfil HPS: {has_hps_profile}')
            
            if has_hps_profile:
                profile = user.hps_profile
                self.stdout.write(self.style.WARNING('\n📋 DATOS DEL MODELO HpsUserProfile:'))
                self.stdout.write(f'  ID: {profile.id}')
                self.stdout.write(f'  Email Verified: {profile.email_verified}')
                self.stdout.write(f'  Is Temp Password: {profile.is_temp_password}')
                self.stdout.write(f'  Must Change Password: {profile.must_change_password}')
                if hasattr(profile, 'created_at'):
                    self.stdout.write(f'  Created At: {profile.created_at}')
                if hasattr(profile, 'updated_at'):
                    self.stdout.write(f'  Updated At: {profile.updated_at}')
                
                # Rol
                if profile.role:
                    self.stdout.write(f'\n  Rol:')
                    self.stdout.write(f'    ID: {profile.role.id}')
                    self.stdout.write(f'    Name: {profile.role.name}')
                    self.stdout.write(f'    Description: {profile.role.description}')
                else:
                    self.stdout.write(self.style.ERROR('  ⚠️  No tiene rol asignado'))
                
                # Equipo
                if profile.team:
                    self.stdout.write(f'\n  Equipo:')
                    self.stdout.write(f'    ID: {profile.team.id}')
                    self.stdout.write(f'    Name: {profile.team.name}')
                    self.stdout.write(f'    Description: {profile.team.description}')
                    self.stdout.write(f'    Is Active: {profile.team.is_active}')
                    if profile.team.team_lead:
                        self.stdout.write(f'    Team Lead: {profile.team.team_lead.email}')
                else:
                    self.stdout.write(self.style.ERROR('  ⚠️  No tiene equipo asignado'))
            else:
                self.stdout.write(self.style.ERROR('\n⚠️  El usuario NO tiene perfil HPS'))
            
            # Verificar relaciones
            self.stdout.write(self.style.WARNING('\n📋 RELACIONES:'))
            
            # HPS Requests
            hps_requests_count = user.hps_requests.count() if hasattr(user, 'hps_requests') else 0
            self.stdout.write(f'  HPS Requests: {hps_requests_count}')
            
            # Chat Conversations
            chat_conversations_count = user.chat_conversations.count() if hasattr(user, 'chat_conversations') else 0
            self.stdout.write(f'  Chat Conversations: {chat_conversations_count}')
            
            # Análisis del problema
            self.stdout.write(self.style.WARNING('\n🔍 ANÁLISIS:'))
            
            if not user.is_active:
                self.stdout.write(self.style.SUCCESS('  ✅ Usuario ya está marcado como inactivo'))
            else:
                self.stdout.write(self.style.ERROR('  ❌ Usuario está activo (is_active=True)'))
            
            if not has_hps_profile:
                self.stdout.write(self.style.ERROR('  ❌ PROBLEMA: Usuario no tiene perfil HPS'))
                self.stdout.write('     Esto puede impedir que se muestre en la gestión de usuarios')
            
            # Verificar permisos para desactivar
            self.stdout.write(self.style.WARNING('\n💡 RECOMENDACIONES:'))
            if user.is_active:
                self.stdout.write('  1. El usuario puede ser desactivado usando:')
                self.stdout.write(f'     POST /api/hps/user/profiles/{profile.id if has_hps_profile else "N/A"}/deactivate/')
                if not has_hps_profile:
                    self.stdout.write('  2. ⚠️  Primero necesita crear un perfil HPS para este usuario')
                    self.stdout.write('     Esto se puede hacer ejecutando el comando de crear usuario nuevamente')
            
            self.stdout.write('\n' + '=' * 80)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())

