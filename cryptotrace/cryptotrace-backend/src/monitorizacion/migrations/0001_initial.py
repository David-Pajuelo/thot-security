# Migración inicial: UserAccessLog en Monitorización (usa tabla existente hps_core_useraccesslog)

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("hps_core", "0009_useraccesslog"),  # La tabla ya existe
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
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
                        "db_table": "hps_core_useraccesslog",
                        "verbose_name": "Registro de acceso",
                        "verbose_name_plural": "Registros de acceso",
                        "ordering": ["-created_at"],
                    },
                ),
            ],
            database_operations=[],  # No crear tabla; ya existe
        ),
    ]
