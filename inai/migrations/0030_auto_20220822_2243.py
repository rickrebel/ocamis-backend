# Generated by Django 2.2.25 on 2022-08-23 03:43

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inai', '0029_auto_20220818_0311'),
    ]

    operations = [
        migrations.AddField(
            model_name='datafile',
            name='all_results',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='Todos los resultados'),
        ),
        migrations.AddField(
            model_name='datafile',
            name='zip_path',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='datafile',
            name='error_process',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='Errores de procesamiento'),
        ),
    ]
