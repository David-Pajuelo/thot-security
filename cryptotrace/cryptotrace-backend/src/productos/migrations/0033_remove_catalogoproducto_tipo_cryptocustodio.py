# Generated manually to remove tipo_cryptocustodio field if it exists

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0032_add_imagen_documento_field'),
    ]

    operations = [
        migrations.RunSQL(
            # SQL para eliminar la columna si existe (PostgreSQL)
            sql="ALTER TABLE productos_catalogoproducto DROP COLUMN IF EXISTS tipo_cryptocustodio;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
