"""
Django settings para producción - CryptoTrace
Extiende settings.py base con validación estricta de variables (sin fallbacks)
"""
from .settings import *
from datetime import timedelta
import sys

# En producción, DEBUG debe ser False
DEBUG = False

# Validación estricta de variables requeridas en producción
REQUIRED_VARS = [
    'SECRET_KEY',
    'FRONTEND_URL',
    'HPS_SYSTEM_URL',
    'ALLOWED_HOSTS',
    'CORS_ALLOWED_ORIGINS',
    'REDIS_HOST',
    'REDIS_URL',
]

missing_vars = [var for var in REQUIRED_VARS if not os.getenv(var)]
if missing_vars:
    error_msg = f"❌ ERROR: Variables de entorno requeridas faltantes en producción: {', '.join(missing_vars)}"
    print(error_msg, file=sys.stderr)
    sys.exit(1)

# Validar que ALLOWED_HOSTS esté configurado
if not ALLOWED_HOSTS:
    print("❌ ERROR: ALLOWED_HOSTS debe estar definida en producción", file=sys.stderr)
    sys.exit(1)

# Validar que CORS_ALLOWED_ORIGINS esté configurado
if not CORS_ALLOWED_ORIGINS:
    print("❌ ERROR: CORS_ALLOWED_ORIGINS debe estar definida en producción", file=sys.stderr)
    sys.exit(1)

# Validar que FRONTEND_URL esté configurado
if not FRONTEND_URL:
    print("❌ ERROR: FRONTEND_URL debe estar definida en producción", file=sys.stderr)
    sys.exit(1)

# Validar que HPS_SYSTEM_URL esté configurado
if not HPS_SYSTEM_URL:
    print("❌ ERROR: HPS_SYSTEM_URL debe estar definida en producción", file=sys.stderr)
    sys.exit(1)

# CORS más estricto en producción
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

# Configuraciones de seguridad para producción
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Clickjacking protection
X_FRAME_OPTIONS = 'DENY'

# REST Framework más estricto en producción
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# JWT más estricto en producción
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'ROTATE_REFRESH_TOKENS': True,
    'ALGORITHM': os.getenv('JWT_ALGORITHM', 'HS256'),
    'SIGNING_KEY': os.getenv('JWT_SECRET_KEY', SECRET_KEY),
}
