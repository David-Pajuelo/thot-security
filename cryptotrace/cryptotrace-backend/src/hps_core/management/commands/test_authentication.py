"""
Script para probar la autenticación JWT con los usuarios creados.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.test import Client
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Prueba la autenticación JWT con usuarios HPS'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('PRUEBA DE AUTENTICACIÓN JWT'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # Usuarios a probar
        test_users = [
            'admin@hps-system.com',
            'jefe@hps.local',
            'lider@hps.local',
            'usuario@hps.local',
        ]

        passwords = {
            'admin@hps-system.com': 'admin123',
            'jefe@hps.local': 'jefe123',
            'lider@hps.local': 'lider123',
            'usuario@hps.local': 'user123',
        }

        client = Client()

        for email in test_users:
            self.stdout.write(f'\n🔐 Probando autenticación para: {email}')
            
            try:
                # Verificar que el usuario existe
                user = User.objects.get(email=email)
                self.stdout.write(f'  ✓ Usuario encontrado en BD')
                
                # Verificar perfil HPS
                if hasattr(user, 'hps_profile'):
                    profile = user.hps_profile
                    self.stdout.write(f'  ✓ Perfil HPS: {profile.role.name}')
                    if profile.team:
                        self.stdout.write(f'  ✓ Equipo: {profile.team.name}')
                else:
                    self.stdout.write(self.style.WARNING('  ⚠ Usuario sin perfil HPS'))
                
                # Probar autenticación con contraseña
                from django.contrib.auth import authenticate
                authenticated_user = authenticate(
                    username=email,
                    password=passwords[email]
                )
                
                if authenticated_user:
                    self.stdout.write(self.style.SUCCESS('  ✓ Autenticación con contraseña: OK'))
                    
                    # Generar token JWT
                    refresh = RefreshToken.for_user(authenticated_user)
                    access_token = str(refresh.access_token)
                    
                    self.stdout.write(self.style.SUCCESS('  ✓ Token JWT generado correctamente'))
                    self.stdout.write(f'    - Access token (primeros 50 chars): {access_token[:50]}...')
                    
                    # Decodificar token para verificar contenido
                    try:
                        import jwt
                        from django.conf import settings
                        from rest_framework_simplejwt.settings import api_settings
                        
                        signing_key = api_settings.SIGNING_KEY
                        algorithm = api_settings.ALGORITHM
                        
                        decoded = jwt.decode(
                            access_token,
                            signing_key,
                            algorithms=[algorithm]
                        )
                        
                        self.stdout.write(f'    - Usuario en token: {decoded.get("username")}')
                        self.stdout.write(f'    - Email en token: {decoded.get("email", "N/A")}')
                        self.stdout.write(f'    - is_superuser: {decoded.get("is_superuser", False)}')
                        self.stdout.write(f'    - must_change_password: {decoded.get("must_change_password", False)}')
                        
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'    ⚠ Error decodificando token: {str(e)}'))
                    
                else:
                    self.stdout.write(self.style.ERROR('  ✗ Autenticación con contraseña: FALLIDA'))
                    self.stdout.write(self.style.ERROR(f'    Contraseña incorrecta o usuario inactivo'))
                
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'  ✗ Usuario no encontrado: {email}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}'))
                import traceback
                self.stdout.write(traceback.format_exc())

        # Probar endpoint de login
        self.stdout.write(self.style.SUCCESS('\n🌐 Probando endpoint de login...'))
        try:
            response = client.post(
                '/api/token/',
                {
                    'username': 'admin@hps.local',
                    'password': 'admin123'
                },
                content_type='application/json'
            )
            
            if response.status_code == 200:
                data = json.loads(response.content)
                self.stdout.write(self.style.SUCCESS('  ✓ Endpoint /api/token/ funciona correctamente'))
                self.stdout.write(f'    - Access token recibido: {"Sí" if "access" in data else "No"}')
                self.stdout.write(f'    - Refresh token recibido: {"Sí" if "refresh" in data else "No"}')
            else:
                self.stdout.write(self.style.ERROR(f'  ✗ Endpoint /api/token/ falló: {response.status_code}'))
                self.stdout.write(f'    Respuesta: {response.content.decode()[:200]}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error probando endpoint: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('Prueba de autenticación completada'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

