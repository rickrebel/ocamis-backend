# Generated by Django 4.1.6 on 2024-05-16 05:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('respond', '0007_remove_datafile_status_process'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='datafile',
            name='file_control',
        ),
        migrations.RemoveField(
            model_name='datafile',
            name='petition',
        ),
    ]
