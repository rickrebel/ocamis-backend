# Generated by Django 2.2.25 on 2022-07-30 01:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inai', '0005_auto_20220729_2024'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datafile',
            name='date',
            field=models.DateField(auto_now_add=True),
        ),
    ]
