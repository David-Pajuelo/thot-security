"""
Modelos de monitorización: registro de accesos HTTP (Django, HPS y Cryptotrace).
"""
from django.conf import settings
from django.db import models


class UserAccessLog(models.Model):
    """
    Registro de acceso HTTP: quién accedió, a qué ruta, cuándo y resultado.
    Aplica a todo el backend (HPS, Cryptotrace, API). Para cumplimiento y trazabilidad.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="access_logs",
        null=True,
        blank=True,
    )
    path = models.CharField(max_length=500, db_index=True)
    method = models.CharField(max_length=10)
    status_code = models.PositiveIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    response_time_ms = models.PositiveIntegerField(
        null=True, blank=True, help_text="Tiempo de respuesta en milisegundos"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hps_core_useraccesslog"  # Tabla existente (migrada desde hps_core)
        verbose_name = "Registro de acceso"
        verbose_name_plural = "Registros de acceso"
        ordering = ["-created_at"]

    def __str__(self):
        user_str = self.user.email if self.user_id else "anon"
        return f"{self.method} {self.path} {self.status_code} ({user_str}) @ {self.created_at:%Y-%m-%d %H:%M}"
