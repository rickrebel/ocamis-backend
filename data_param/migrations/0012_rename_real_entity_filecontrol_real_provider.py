# Generated by Django 4.1.6 on 2024-03-26 20:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_param', '0011_remove_filecontrol_format_file_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='filecontrol',
            old_name='real_entity',
            new_name='real_provider',
        ),
    ]
