# Generated by Django 4.1.6 on 2023-07-29 08:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_param', '0006_filecontrol_real_entity'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='collection',
            options={'ordering': ['app_label', 'name'], 'verbose_name': 'Modelo (Colección)', 'verbose_name_plural': '1.3 Modelos (Colecciones)'},
        ),
    ]
