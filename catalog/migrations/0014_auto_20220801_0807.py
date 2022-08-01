# Generated by Django 2.2.25 on 2022-08-01 13:07

import catalog.models
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0013_auto_20220801_0147'),
    ]

    operations = [
        migrations.AddField(
            model_name='state',
            name='alternative_names',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=catalog.models.State.default_alternative_names, help_text='Ocupar para OCAMIS', verbose_name='Lista nombres alternativos'),
        ),
        migrations.AlterField(
            model_name='state',
            name='other_names',
            field=models.CharField(blank=True, help_text='No utilizar para OCAMIS, es solo para para cero desabasto', max_length=255, null=True, verbose_name='Otros nombres'),
        ),
    ]
