# Generated by Django 4.1.6 on 2024-03-26 21:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0018_alter_asynctask_data_file_alter_asynctask_reply_file_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='asynctask',
            old_name='entity',
            new_name='provider',
        ),
        migrations.RenameField(
            model_name='cutoff',
            old_name='entity',
            new_name='provider',
        ),
    ]
