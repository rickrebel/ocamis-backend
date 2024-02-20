# Generated by Django 4.1.6 on 2024-02-19 23:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_param', '0010_namecolumn_destination'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='filecontrol',
            name='format_file',
        ),
        migrations.RemoveField(
            model_name='filecontrol',
            name='in_percent',
        ),
        migrations.AddField(
            model_name='filecontrol',
            name='is_intermediary',
            field=models.BooleanField(default=False, verbose_name='Es intermediario entre archivos'),
        ),
    ]
