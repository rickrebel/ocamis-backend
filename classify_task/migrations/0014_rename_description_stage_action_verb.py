# Generated by Django 4.1.6 on 2023-10-30 16:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('classify_task', '0013_remove_statustask_description_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='stage',
            old_name='description',
            new_name='action_verb',
        ),
    ]
