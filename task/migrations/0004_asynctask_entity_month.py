# Generated by Django 4.1.6 on 2023-05-19 06:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inai', '0023_rename_months_agency_petition_entity_months'),
        ('task', '0003_remove_asynctask_week_entity_asynctask_entity_week'),
    ]

    operations = [
        migrations.AddField(
            model_name='asynctask',
            name='entity_month',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='async_tasks', to='inai.entitymonth'),
        ),
    ]
