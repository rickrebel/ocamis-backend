# Generated by Django 2.2.25 on 2022-07-31 05:47

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0003_auto_20220729_1956'),
    ]

    operations = [
        migrations.AddField(
            model_name='filetype',
            name='addl_params',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
