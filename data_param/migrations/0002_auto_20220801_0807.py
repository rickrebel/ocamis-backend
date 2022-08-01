# Generated by Django 2.2.25 on 2022-08-01 13:07

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data_param', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='finalfield',
            options={'verbose_name': 'Campo final', 'verbose_name_plural': 'Campos finales (en DB)'},
        ),
        migrations.RemoveField(
            model_name='finalfield',
            name='variatrions',
        ),
        migrations.AddField(
            model_name='finalfield',
            name='dashboard_hide',
            field=models.BooleanField(default=False, help_text='Ocultar en el dashboard (es complementaria o equivalente)', verbose_name='Oculta en dashboard'),
        ),
        migrations.AddField(
            model_name='finalfield',
            name='in_data_base',
            field=models.BooleanField(default=False, help_text='Ya está en la base de datos comprobado', verbose_name='Verificado (solo devs)'),
        ),
        migrations.AddField(
            model_name='finalfield',
            name='variations',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, help_text='Nombres como pueden venir en las tablas de INAI', null=True, verbose_name='Otros posibles nombres (variaciones)'),
        ),
        migrations.AlterField(
            model_name='collection',
            name='data_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_param.DataGroup', verbose_name='Conjunto de datos'),
        ),
        migrations.AlterField(
            model_name='collection',
            name='name',
            field=models.CharField(help_text='Nombre del Modelo público (Meta.verbose_name_plural)', max_length=225, verbose_name='verbose_name_plural'),
        ),
        migrations.AlterField(
            model_name='finalfield',
            name='addl_params',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, help_text='Por ejemplo, max_length, null, blank, help_text, así como otras configuraciones que se nos vayan ocurriendo', null=True, verbose_name='Otras configuraciones'),
        ),
        migrations.AlterField(
            model_name='finalfield',
            name='name',
            field=models.CharField(max_length=120, verbose_name='Nombre del campo en BD'),
        ),
        migrations.AlterField(
            model_name='finalfield',
            name='verbose_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='finalfield',
            name='verified',
            field=models.BooleanField(default=False, help_text='Ricardo ya verificó que todos los parámetros están bien', verbose_name='Verificado (solo rick)'),
        ),
    ]
