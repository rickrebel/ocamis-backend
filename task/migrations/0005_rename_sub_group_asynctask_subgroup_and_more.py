# Generated by Django 4.1.6 on 2023-02-20 22:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0004_remove_asynctask_date_send_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='asynctask',
            old_name='sub_group',
            new_name='subgroup',
        ),
        migrations.AddField(
            model_name='asynctask',
            name='is_current',
            field=models.BooleanField(default=True, verbose_name='Es la última tarea'),
        ),
    ]
