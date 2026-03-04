# RBAC: modelo HpsPermission y relación M2M HpsRole.granted_permissions

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hps_core", "0006_hpsuserprofile_default_team"),
    ]

    operations = [
        migrations.CreateModel(
            name="HpsPermission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("codename", models.CharField(help_text="Identificador único del permiso (ej: hps.gestionar_roles)", max_length=100, unique=True)),
                ("name", models.CharField(help_text="Descripción legible del permiso", max_length=255)),
                ("category", models.CharField(blank=True, help_text="Ej: hps, productos, chat", max_length=50)),
            ],
            options={
                "verbose_name": "Permiso HPS",
                "verbose_name_plural": "Permisos HPS",
                "ordering": ["category", "codename"],
            },
        ),
        migrations.AddField(
            model_name="hpsrole",
            name="granted_permissions",
            field=models.ManyToManyField(
                blank=True,
                related_name="roles",
                to="hps_core.hpspermission",
                verbose_name="Permisos concedidos",
            ),
        ),
    ]
