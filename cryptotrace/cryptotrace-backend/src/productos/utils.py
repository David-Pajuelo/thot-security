import random
import string
import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

def generar_password_temporal():
    """
    Genera una contraseña temporal legible y segura.
    Formato: 3 palabras + 3 números
    Ejemplo: Casa2024Azul456
    """
    palabras = [
        'Casa', 'Azul', 'Sol', 'Mar', 'Luna', 'Rio', 'Flor', 'Arbol',
        'Gato', 'Perro', 'Libro', 'Mesa', 'Silla', 'Puerta', 'Ventana', 'Coche',
        'Cielo', 'Tierra', 'Fuego', 'Agua', 'Viento', 'Roca', 'Pez', 'Ave'
    ]
    
    # Seleccionar 2 palabras aleatorias
    palabra1 = random.choice(palabras)
    palabra2 = random.choice(palabras)
    
    # Generar 3 números aleatorios
    numeros = ''.join(random.choices(string.digits, k=3))
    
    # Combinar: Palabra + Números + Palabra
    password = f"{palabra1}{numeros}{palabra2}"
    
    return password

def enviar_email_nuevo_usuario(user: User, password_temporal: str):
    """
    Envía un email con las credenciales de acceso a un nuevo usuario.
    
    Args:
        user: Instancia del usuario Django
        password_temporal: Contraseña temporal generada
    
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        # Verificar que el usuario tenga email
        if not user.email:
            logger.warning(f"Usuario {user.username} no tiene email configurado")
            return False
            
        # Verificar configuración de email
        if not settings.EMAIL_HOST_USER:
            logger.warning("EMAIL_HOST_USER no configurado en settings")
            return False
            
        # Preparar contexto para el template
        context = {
            'username': user.username,
            'password': password_temporal,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'frontend_url': settings.FRONTEND_URL,
        }
        
        # Renderizar templates
        subject = f'🔐 Bienvenido a CryptoTrace - Credenciales de Acceso'
        html_message = render_to_string('emails/nuevo_usuario.html', context)
        # Generar mensaje de texto plano simple
        plain_message = f"""
Bienvenido a CryptoTrace - IDIAICOX

Hola {user.first_name or user.username},

Se ha creado tu cuenta de acceso a CryptoTrace.

Credenciales de acceso:
- Usuario: {user.username}
- Contraseña temporal: {password_temporal}

Accede a la plataforma en: {settings.FRONTEND_URL}

Por seguridad, deberás cambiar tu contraseña en el primer acceso.

Saludos,
Equipo CryptoTrace - IDIAICOX
        """.strip()
        
        # Enviar email
        resultado = send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        if resultado:
            logger.info(f"Email enviado exitosamente a {user.email}")
            return True
        else:
            logger.error(f"Error enviando email a {user.email}")
            return False
            
    except Exception as e:
        logger.error(f"Error enviando email a {user.username}: {str(e)}")
        return False 