from django.apps import AppConfig


class HpsCoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hps_core"
    verbose_name = "Habilitación Personal de Seguridad"

    def ready(self):
        from . import signals  # noqa: F401

