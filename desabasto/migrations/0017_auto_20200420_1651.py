# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2020-04-20 21:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('desabasto', '0016_auto_20200408_1729'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='institution_raw',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Instituci\xf3n escrita'),
        ),
        migrations.AlterField(
            model_name='report',
            name='origin_app',
            field=models.CharField(default='CD2', max_length=100, verbose_name='Aplicacion'),
        ),
        migrations.AlterField(
            model_name='responsable',
            name='institution',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responsables', to='desabasto.Institution'),
        ),
        migrations.AlterField(
            model_name='supply',
            name='report',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supplies', to='desabasto.Report'),
        ),
    ]
