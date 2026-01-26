# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0032_add_imagen_documento_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='lineatemporalproducto',
            name='tipo_cryptocustodio',
            field=models.CharField(
                choices=[('c', 'c'), ('CC', 'CC'), ('Ninguno', 'Ninguno')],
                default='Ninguno',
                help_text='Tipo de cryptocustodio seleccionado por el usuario: c, CC o Ninguno',
                max_length=10
            ),
        ),
        migrations.AlterField(
            model_name='lineatemporalproducto',
            name='cc',
            field=models.IntegerField(
                default=1,
                help_text='CC del AC21 (columna del PDF): 1, 2, 3 o vacío. Viene del OCR y NO debe modificarse.'
            ),
        ),
    ]
