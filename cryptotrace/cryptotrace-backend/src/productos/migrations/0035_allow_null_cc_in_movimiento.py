# Generated manually to allow NULL values in MovimientoProducto.cc

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0034_replace_cc_with_tipo_producto'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movimientoproducto',
            name='cc',
            field=models.IntegerField(blank=True, help_text='Campo CC del AC-21 (Accounting Legend Code) - Informativo del documento, puede estar vacío', null=True),
        ),
    ]
