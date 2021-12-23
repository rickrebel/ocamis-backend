# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2021-01-26 22:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('desabasto', '0031_auto_20210126_1403'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='supply',
            name='presentation',
        ),
        migrations.AddField(
            model_name='presentation',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='presentation',
            name='presentation_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='desabasto.PresentationType'),
        ),
        migrations.AddField(
            model_name='presentation',
            name='presentation_type_raw',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='supply',
            name='container',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='desabasto.Container'),
        ),
        migrations.AlterField(
            model_name='presentation',
            name='clave',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='presentation',
            name='official_name',
            field=models.TextField(blank=True, null=True),
        ),
    ]
