"""
ASGI config for cryptotrace_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cryptotrace_backend.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import WebSocket routing after Django is initialized
# Importar con try/except para evitar errores si la app aún no está completamente configurada
try:
    from hps_agent.routing import websocket_urlpatterns
    websocket_routing = AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    )
except ImportError:
    # Si la app aún no está lista, usar routing vacío
    websocket_routing = URLRouter([])

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": websocket_routing,
})
