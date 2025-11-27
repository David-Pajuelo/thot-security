from django.core.management.base import BaseCommand
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings


class Command(BaseCommand):
    help = 'Prueba la conexión SMTP directamente'

    def add_arguments(self, parser):
        parser.add_argument('--to', type=str, help='Email de destino')

    def handle(self, *args, **options):
        to_email = options['to'] or 'carlos.alonso@techex.es'
        
        self.stdout.write(f"🔧 Probando conexión SMTP directa...")
        self.stdout.write(f"📧 Host: {settings.EMAIL_HOST}")
        self.stdout.write(f"📧 Puerto: {settings.EMAIL_PORT}")
        self.stdout.write(f"📧 Usuario: {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"📧 TLS: {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"📧 SSL: {settings.EMAIL_USE_SSL}")
        
        try:
            # Crear mensaje simple
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_HOST_USER
            msg['To'] = to_email
            msg['Subject'] = "Prueba SMTP Directa - CryptoTrace"
            
            body = "Esta es una prueba de conexión SMTP directa desde CryptoTrace."
            msg.attach(MIMEText(body, 'plain'))
            
            # Conectar al servidor
            if settings.EMAIL_USE_SSL:
                self.stdout.write("🔐 Conectando con SSL...")
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT, context=context)
            else:
                self.stdout.write("🔐 Conectando con TLS...")
                server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
                if settings.EMAIL_USE_TLS:
                    server.starttls()
            
            self.stdout.write("✅ Conexión establecida")
            
            # Autenticar
            self.stdout.write("🔑 Intentando autenticación...")
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            self.stdout.write("✅ Autenticación exitosa")
            
            # Enviar
            self.stdout.write("📤 Enviando email...")
            text = msg.as_string()
            server.sendmail(settings.EMAIL_HOST_USER, to_email, text)
            self.stdout.write(f"✅ Email enviado exitosamente a {to_email}")
            
            server.quit()
            
        except smtplib.SMTPAuthenticationError as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error de autenticación: {e}")
            )
            self.stdout.write(
                self.style.WARNING("💡 Verifica usuario y contraseña en el panel de PrivateEmail")
            )
        except smtplib.SMTPConnectError as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error de conexión: {e}")
            )
            self.stdout.write(
                self.style.WARNING("💡 Verifica host y puerto")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error: {e}")
            ) 