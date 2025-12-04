"""
ASGI config for cryptotrace_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
import logging
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cryptotrace_backend.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import WebSocket routing after Django is initialized
# Importar con try/except para evitar errores si la app aún no está completamente configurada
try:
    from hps_agent.routing import websocket_urlpatterns
    from django.conf import settings
    
    logger.info(f"✅ WebSocket routing cargado: {len(websocket_urlpatterns)} patrones")
    for pattern in websocket_urlpatterns:
        logger.info(f"   - {pattern.pattern}")
    
    # En desarrollo, permitir todos los orígenes para WebSocket
    # En producción, usar AllowedHostsOriginValidator
    if settings.DEBUG:
        websocket_routing = AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
        logger.info("✅ WebSocket routing configurado para desarrollo (sin validación de origen)")
    else:
        websocket_routing = AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(websocket_urlpatterns)
            )
        )
        logger.info("✅ WebSocket routing configurado para producción (con validación de origen)")
except ImportError as e:
    # Si la app aún no está lista, usar routing vacío
    logger.warning(f"⚠️ No se pudo cargar WebSocket routing: {e}")
    websocket_routing = URLRouter([])

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": websocket_routing,
})

logger.info("✅ ASGI application configurada correctamente")
