# Generated by Django 4.1.6 on 2023-05-19 06:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inai', '0020_entityweek_remove_weekentity_entity_and_more'),
        ('task', '0002_asynctask_week_entity'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='asynctask',
            name='week_entity',
        ),
        migrations.AddField(
            model_name='asynctask',
            name='entity_week',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='async_tasks', to='inai.entityweek'),
        ),
    ]
