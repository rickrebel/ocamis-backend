# Generated by Django 2.2.25 on 2022-07-26 19:23

import data_param.models
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=225)),
                ('model_name', models.CharField(max_length=225, verbose_name='Nombre en el código')),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Modelo (Tabla)',
                'verbose_name_plural': 'Modelos o Tablas',
            },
        ),
        migrations.CreateModel(
            name='DataGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80)),
                ('is_default', models.BooleanField(default=False)),
                ('can_has_percent', models.BooleanField(default=False, verbose_name='Puede tener porcentajes')),
            ],
            options={
                'verbose_name': 'Grupo de datos',
                'verbose_name_plural': 'Grupos de datos',
            },
        ),
        migrations.CreateModel(
            name='DataType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=225)),
                ('description', models.TextField(blank=True, null=True)),
                ('addl_params', django.contrib.postgres.fields.jsonb.JSONField(default=data_param.models.DataType.default_params_data_type, verbose_name='Otras configuraciones')),
                ('is_common', models.BooleanField(default=True)),
                ('order', models.IntegerField(default=1)),
            ],
            options={
                'verbose_name': 'Tipo de dato',
                'verbose_name_plural': 'Tipos de datos',
            },
        ),
        migrations.CreateModel(
            name='FinalField',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('verbose_name', models.TextField(blank=True, null=True)),
                ('addl_params', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='Otras configuraciones')),
                ('variatrions', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='Otros posibles nombres')),
                ('requiered', models.BooleanField(default=False, verbose_name='Es indispensable para registrar fila')),
                ('is_common', models.BooleanField(default=False, verbose_name='Es una variable muy común')),
                ('verified', models.BooleanField(default=False, verbose_name='Verificado (solo devs)')),
                ('collection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_param.Collection')),
                ('data_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='data_param.DataType')),
            ],
            options={
                'verbose_name': 'Documento final',
                'verbose_name_plural': 'Documentos finales',
            },
        ),
        migrations.AddField(
            model_name='collection',
            name='data_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_param.DataGroup'),
        ),
        migrations.CreateModel(
            name='CleanFunction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80)),
                ('public_name', models.CharField(blank=True, max_length=120, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('priority', models.SmallIntegerField(default=5, verbose_name='Nivel de prioridad (5 niveles)')),
                ('for_all_data', models.BooleanField(default=False, verbose_name='Es una tranformación para toda la info')),
                ('addl_params', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='Otras configuraciones')),
                ('restricted_field', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='data_param.FinalField', verbose_name='Campo final al cual solo puede aplicarse')),
            ],
            options={
                'verbose_name': 'Función de limpieza y tranformación',
                'verbose_name_plural': 'Funciones de limpieza y tranformación',
            },
        ),
    ]
