# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2021-03-09 06:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('desabasto', '0037_auto_20210308_1822'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supply',
            name='medicine_name_raw',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Nombre reportado del medicamento'),
        ),
    ]
