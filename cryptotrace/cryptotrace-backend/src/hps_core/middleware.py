"""
Middleware para registro de accesos HTTP (UserAccessLog).
"""
import time
import logging

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

# Rutas que no se registran para evitar saturar (estáticos, health, etc.)
ACCESS_LOG_SKIP_PREFIXES = (
    "/static/",
    "/media/",
    "/favicon.ico",
    "/__debug__",
)


def get_client_ip(request):
    """Obtener IP del cliente (respeta X-Forwarded-For si hay proxy)."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or ""


class AccessLogMiddleware(MiddlewareMixin):
    """
    Registra cada petición HTTP en UserAccessLog (user, path, method, status_code, ip, user_agent, tiempo).
    Se puede desactivar con ACCESS_LOG_ENABLED = False en settings.
    """

    def process_request(self, request):
        if getattr(settings, "ACCESS_LOG_ENABLED", True) and not self._should_skip(request):
            request._access_log_start = time.time()
        return None

    def process_response(self, request, response):
        if not getattr(settings, "ACCESS_LOG_ENABLED", True):
            return response
        if self._should_skip(request):
            return response
        start = getattr(request, "_access_log_start", None)
        if start is None:
            return response

        response_time_ms = None
        if start is not None:
            response_time_ms = int((time.time() - start) * 1000)

        try:
            UserAccessLog = __import__("hps_core.models", fromlist=["UserAccessLog"]).UserAccessLog
            user = getattr(request, "user", None)
            if user and not user.is_authenticated:
                user = None
            UserAccessLog.objects.create(
                user=user,
                path=request.path[:500],
                method=request.method[:10],
                status_code=response.status_code,
                ip_address=get_client_ip(request) or None,
                user_agent=request.META.get("HTTP_USER_AGENT") or "",
                response_time_ms=response_time_ms,
            )
        except Exception as e:
            logger.warning("AccessLogMiddleware: no se pudo guardar registro: %s", e)

        return response

    def _should_skip(self, request):
        path = request.path
        for prefix in ACCESS_LOG_SKIP_PREFIXES:
            if path.startswith(prefix):
                return True
        return False
