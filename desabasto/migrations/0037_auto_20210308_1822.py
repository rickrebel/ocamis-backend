# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-03-09 00:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('desabasto', '0036_auto_20210227_1600'),
    ]

    operations = [
        migrations.AddField(
            model_name='component',
            name='short_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='container',
            name='presentation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='containers', to='desabasto.Presentation'),
        ),
    ]
