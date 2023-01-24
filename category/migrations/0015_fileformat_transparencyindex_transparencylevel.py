# Generated by Django 2.2.25 on 2022-10-24 14:52

import category.models
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0014_auto_20220914_2140'),
    ]

    operations = [
        migrations.CreateModel(
            name='FileFormat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=20)),
                ('public_name', models.CharField(max_length=80)),
                ('suffixes', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=category.models.default_list, null=True, verbose_name='extensiones')),
                ('readable', models.BooleanField(verbose_name='es legible por máquinas')),
                ('addl_params', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=category.models.default_dict)),
                ('name', models.CharField(max_length=255)),
                ('extension', models.CharField(max_length=80)),
                ('is_default', models.BooleanField(default=False)),
                ('has_data', models.BooleanField(verbose_name='Tiene datos procesables')),
                ('icon', models.CharField(max_length=80)),
            ],
            options={
                'verbose_name': 'Formato de documento',
                'verbose_name_plural': 'Formato de documentos',
            },
        ),
        migrations.CreateModel(
            name='TransparencyIndex',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=20)),
                ('public_name', models.CharField(max_length=80)),
                ('description', models.TextField(blank=True, null=True)),
                ('scheme_color', models.CharField(blank=True, max_length=90, null=True, verbose_name='Esquema de color')),
                ('viz_params', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=category.models.default_dict)),
            ],
            options={
                'verbose_name': 'Indicador de Transparencia',
                'verbose_name_plural': 'Indicadores de Transparencia',
            },
        ),
        migrations.CreateModel(
            name='TransparencyLevel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=20)),
                ('public_name', models.CharField(max_length=80)),
                ('value', models.IntegerField(default=0, help_text='Para ordenar y decidier según menor')),
                ('description', models.TextField(blank=True, null=True)),
                ('other_conditions', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=category.models.default_list)),
                ('color', models.CharField(blank=True, max_length=20, null=True)),
                ('anomalies', models.ManyToManyField(blank=True, to='category.Anomaly', verbose_name='Anomalías relacionadas')),
                ('file_formats', models.ManyToManyField(blank=True, to='category.FileFormat', verbose_name='Formatos de archivo')),
                ('final_level', models.ForeignKey(blank=True, help_text='Si existe, se va a ese nivel de indicador principal', null=True, on_delete=django.db.models.deletion.CASCADE, to='category.TransparencyLevel', verbose_name='nivel principal')),
                ('transparency_index', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='category.TransparencyIndex', verbose_name='Indicador de Transparencia')),
            ],
        ),
    ]
