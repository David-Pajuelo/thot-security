# Registro de accesos HTTP (UserAccessLog) para criterios de calidad y trazabilidad

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("hps_core", "0008_populate_rbac_permissions"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserAccessLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("path", models.CharField(db_index=True, max_length=500)),
                ("method", models.CharField(max_length=10)),
                ("status_code", models.PositiveIntegerField(blank=True, null=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                ("response_time_ms", models.PositiveIntegerField(blank=True, help_text="Tiempo de respuesta en milisegundos", null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="access_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Registro de acceso",
                "verbose_name_plural": "Registros de acceso",
                "ordering": ["-created_at"],
            },
        ),
    ]
