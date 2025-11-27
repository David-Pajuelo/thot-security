from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from productos.utils import generar_password_temporal, enviar_email_nuevo_usuario


class Command(BaseCommand):
    help = 'Prueba el envío de emails de bienvenida'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email de destino para la prueba')
        parser.add_argument('--username', type=str, default='usuario_prueba', help='Nombre de usuario para la prueba')

    def handle(self, *args, **options):
        email = options['email']
        username = options['username']
        
        if not email:
            self.stdout.write(
                self.style.ERROR('❌ Debes proporcionar un email con --email ejemplo@gmail.com')
            )
            return
            
        # Crear usuario temporal para la prueba
        try:
            # Verificar si ya existe y eliminarlo
            if User.objects.filter(username=username).exists():
                User.objects.filter(username=username).delete()
                self.stdout.write(f"🗑️ Usuario {username} eliminado para la prueba")
            
            # Crear usuario temporal
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name='Usuario',
                last_name='Prueba'
            )
            
            # Generar contraseña temporal
            password_temporal = generar_password_temporal()
            
            self.stdout.write(f"📧 Enviando email de prueba a: {email}")
            self.stdout.write(f"👤 Usuario: {username}")
            self.stdout.write(f"🔑 Contraseña temporal: {password_temporal}")
            
            # Enviar email
            resultado = enviar_email_nuevo_usuario(user, password_temporal)
            
            if resultado:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Email enviado exitosamente a {email}')
                )
                self.stdout.write(
                    self.style.WARNING('⚠️ Revisa tu bandeja de entrada (y spam/promociones)')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error enviando email a {email}')
                )
                self.stdout.write(
                    self.style.WARNING('💡 Verifica la configuración de EMAIL en settings.py')
                )
            
            # Limpiar usuario de prueba
            user.delete()
            self.stdout.write(f"🗑️ Usuario de prueba {username} eliminado")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            ) 