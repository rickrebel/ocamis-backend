# Generated by Django 4.1.6 on 2024-06-11 19:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0024_alter_cutoff_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='filepath',
            options={'ordering': ['-id'], 'verbose_name': 'Ruta de archivo', 'verbose_name_plural': 'Rutas de archivo'},
        ),
        migrations.AlterModelOptions(
            name='platform',
            options={'verbose_name': 'Plataforma', 'verbose_name_plural': 'Plataformas'},
        ),
        migrations.AlterModelTable(
            name='platform',
            table='rds_platform',
        ),
    ]
