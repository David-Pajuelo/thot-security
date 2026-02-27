# Migración: equipo predeterminado para solicitudes HPS (jefe seguridad / líder con varios equipos)

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("hps_core", "0005_populate_team_memberships_from_profile"),
    ]

    operations = [
        migrations.AddField(
            model_name="hpsuserprofile",
            name="default_team",
            field=models.ForeignKey(
                blank=True,
                help_text="Equipo predeterminado para solicitudes HPS (p. ej. jefe seguridad: 'envía solicitud a correo').",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="profiles_default_team",
                to="hps_core.hpsteam",
            ),
        ),
    ]
