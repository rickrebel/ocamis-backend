# Generated by Django 4.1.6 on 2024-05-04 21:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_param', '0018_filecontrol_status_register'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='filecontrol',
            name='old_status_register',
        ),
    ]
