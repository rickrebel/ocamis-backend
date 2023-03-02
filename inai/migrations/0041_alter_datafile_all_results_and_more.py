# Generated by Django 4.1.5 on 2023-01-22 07:41

from django.db import migrations, models

import data_param.models
import inai.models


class Migration(migrations.Migration):

    dependencies = [
        ('inai', '0040_auto_20221206_1417'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datafile',
            name='all_results',
            field=models.JSONField(blank=True, null=True, verbose_name='Todos los resultados'),
        ),
        migrations.AlterField(
            model_name='datafile',
            name='error_process',
            field=models.JSONField(blank=True, null=True, verbose_name='Errores de procesamiento'),
        ),
        migrations.AlterField(
            model_name='datafile',
            name='explore_data',
            field=models.JSONField(blank=True, default=inai.models.default_explore_data, null=True, verbose_name='Primeros datos, de exploración'),
        ),
        migrations.AlterField(
            model_name='filecontrol',
            name='addl_params',
            field=models.JSONField(),
        ),
        migrations.AlterField(
            model_name='filecontrol',
            name='final_data',
            field=models.BooleanField(blank=True, null=True, verbose_name='Es información final'),
        ),
        migrations.AlterField(
            model_name='namecolumn',
            name='clean_params',
            field=models.JSONField(blank=True, null=True, verbose_name='Parámetros de limpieza'),
        ),
        migrations.AlterField(
            model_name='petition',
            name='ask_extension',
            field=models.BooleanField(blank=True, null=True, verbose_name='Se solicitó extensión'),
        ),
        migrations.AlterField(
            model_name='petition',
            name='info_queja_inai',
            field=models.JSONField(blank=True, help_text='Información de la queja en INAI Seach', null=True, verbose_name='Datos de queja'),
        ),
        migrations.AlterField(
            model_name='processfile',
            name='addl_params',
            field=models.JSONField(blank=True, null=True, verbose_name='Otras configuraciones'),
        ),
        migrations.AlterField(
            model_name='transformation',
            name='addl_params',
            field=models.JSONField(blank=True, default=data_param.models.default_addl_params, null=True),
        ),
    ]
