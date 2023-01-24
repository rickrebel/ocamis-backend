# Generated by Django 2.2.25 on 2022-07-11 15:41

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0006_auto_20220323_1545'),
    ]

    operations = [
        migrations.CreateModel(
            name='Entity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('addl_params', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('vigencia', models.BooleanField(default=True)),
                ('clues', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalog.CLUES')),
                ('institution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.Institution')),
                ('state', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalog.State')),
            ],
            options={
                'verbose_name': 'Sujeto Obligado',
                'verbose_name_plural': 'Sujetos Obligados',
            },
        ),
    ]
