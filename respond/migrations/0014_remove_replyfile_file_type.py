# Generated by Django 4.1.6 on 2024-07-14 19:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('respond', '0013_alter_sheetfile_options_datafile_sample_file_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='replyfile',
            name='file_type',
        ),
    ]
