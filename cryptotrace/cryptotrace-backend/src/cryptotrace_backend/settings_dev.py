"""
Django settings para desarrollo - CryptoTrace
Extiende settings.py base con fallbacks a localhost para desarrollo local
"""
from .settings import *

# En desarrollo, permitir fallbacks a localhost si no están definidas las variables
DEBUG = True

# Fallbacks para desarrollo local
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "backend", "cryptotrace-backend", "*"]

if not CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://cryptotrace-backend:8080",
        "http://cryptotrace-processing:5001",
    ]
    CORS_ALLOW_ALL_ORIGINS = True

# Fallbacks para URLs en desarrollo
if not FRONTEND_URL:
    FRONTEND_URL = 'http://localhost:3000'

if not HPS_SYSTEM_URL:
    HPS_SYSTEM_URL = 'http://localhost:3001'

if not NEXT_PUBLIC_HPS_SYSTEM_URL:
    NEXT_PUBLIC_HPS_SYSTEM_URL = 'http://localhost:3001'

# Fallbacks para Redis en desarrollo
if not REDIS_HOST:
    REDIS_HOST = "localhost"

if not REDIS_URL:
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# Fallback para SECRET_KEY en desarrollo (solo si no está definida)
if not SECRET_KEY:
    SECRET_KEY = 'django-insecure-dev-key-change-in-production'

# Configuración específica de desarrollo
CORS_ALLOW_CREDENTIALS = True

