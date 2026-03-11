# UserAccessLog movido a la app monitorizacion (tabla se mantiene)

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("hps_core", "0009_useraccesslog"),
        ("monitorizacion", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name="UserAccessLog"),
            ],
            database_operations=[],  # No borrar la tabla
        ),
    ]
