# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2021-01-21 23:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('desabasto', '0026_auto_20210121_1315'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='public_testimony',
            field=models.NullBooleanField(),
        ),
    ]
