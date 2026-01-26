# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0033_add_tipo_cryptocustodio'),
    ]

    operations = [
        migrations.AddField(
            model_name='catalogoproducto',
            name='tipo_cryptocustodio',
            field=models.CharField(
                choices=[('c', 'c'), ('CC', 'CC'), ('Ninguno', 'Ninguno')],
                default='Ninguno',
                help_text='Tipo de cryptocustodio por defecto para este producto: c, CC o Ninguno',
                max_length=10
            ),
        ),
    ]
