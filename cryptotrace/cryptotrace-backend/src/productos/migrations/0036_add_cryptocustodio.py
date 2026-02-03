# Generated for Cryptocustodios feature (1-N with Empresa)

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0035_allow_null_cc_in_movimiento'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cryptocustodio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('empleo_rango', models.CharField(blank=True, max_length=100, null=True, verbose_name='Empleo/Rango')),
                ('nombre_apellidos', models.CharField(max_length=200, verbose_name='Nombre y Apellidos')),
                ('cargo', models.CharField(blank=True, max_length=100, null=True, verbose_name='Cargo')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cryptocustodios', to='productos.empresa', verbose_name='Empresa')),
            ],
            options={
                'verbose_name': 'Cryptocustodio',
                'verbose_name_plural': 'Cryptocustodios',
                'ordering': ['empresa', 'nombre_apellidos'],
            },
        ),
    ]
