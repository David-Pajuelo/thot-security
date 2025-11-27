from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0021_alter_albaran_tipo_documento'),
    ]

    operations = [
        migrations.AddField(
            model_name='albaran',
            name='accesorios',
            field=models.JSONField(
                blank=True, 
                null=True,
                default=dict,
                help_text='Lista de accesorios incluidos en el AC21'
            ),
        ),
        migrations.AddField(
            model_name='albaran',
            name='equipos_prueba',
            field=models.JSONField(
                blank=True, 
                null=True,
                default=dict,
                help_text='Lista de equipos de prueba incluidos en el AC21'
            ),
        ),
    ] 