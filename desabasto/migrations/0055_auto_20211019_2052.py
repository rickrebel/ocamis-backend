# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2021-10-20 01:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('desabasto', '0054_auto_20211019_1738'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecipeMedicine2',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_emision', models.DateTimeField(blank=True, null=True)),
                ('fecha_entrega', models.DateTimeField(blank=True, null=True)),
                ('clave_medicamento', models.CharField(blank=True, max_length=20, null=True)),
                ('cantidad_prescrita', models.IntegerField(blank=True, null=True)),
                ('cantidad_entregada', models.IntegerField(blank=True, null=True)),
                ('precio_medicamento', models.FloatField(blank=True, null=True)),
                ('rn', models.IntegerField(blank=True, null=True)),
                ('delivered', models.CharField(blank=True, max_length=3, null=True)),
            ],
            options={
                'verbose_name': 'RecipeItem',
                'verbose_name_plural': 'RecipeItems',
            },
        ),
        migrations.CreateModel(
            name='RecipeReport2',
            fields=[
                ('folio_documento', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('year_month', models.IntegerField(blank=True, null=True)),
                ('clave_presupuestal', models.CharField(blank=True, max_length=20, null=True)),
                ('nivel_atencion', models.IntegerField(blank=True, null=True)),
                ('delivered', models.CharField(blank=True, max_length=3, null=True)),
                ('anomaly', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'RecipeReport2',
                'verbose_name_plural': 'RecipeReports2',
            },
        ),
        migrations.CreateModel(
            name='RecipeReportLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_name', models.TextField()),
                ('processing_date', models.DateTimeField(auto_now=True)),
                ('errors', models.TextField(blank=True, null=True)),
                ('successful', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'RecipeReportLog',
                'verbose_name_plural': 'RecipeReportLogs',
            },
        ),
        migrations.DeleteModel(
            name='RecipeReportRaw',
        ),
        migrations.AddField(
            model_name='clues',
            name='rr_data',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='container',
            name='is_current',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='container',
            name='origen_cvmei',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='container',
            name='presentation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='containers', to='desabasto.Presentation'),
        ),
        migrations.AlterField(
            model_name='container',
            name='short_name',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='medic',
            name='clave_medico',
            field=models.CharField(max_length=30, primary_key=True, serialize=False),
        ),
        migrations.AddField(
            model_name='recipereport2',
            name='clues',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='desabasto.CLUES'),
        ),
        migrations.AddField(
            model_name='recipereport2',
            name='delegacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='desabasto.State'),
        ),
        migrations.AddField(
            model_name='recipereport2',
            name='medico',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='desabasto.Medic'),
        ),
        migrations.AddField(
            model_name='recipereport2',
            name='tipo_documento',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='desabasto.DocumentType'),
        ),
        migrations.AddField(
            model_name='recipemedicine2',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='desabasto.RecipeReport2'),
        ),
    ]
