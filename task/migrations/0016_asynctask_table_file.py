# Generated by Django 4.1.6 on 2023-03-16 18:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inai', '0058_remove_datafile_sheets_info_datafile_filtered_sheets_and_more'),
        ('task', '0015_alter_asynctask_status_task_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='asynctask',
            name='table_file',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='async_tasks', to='inai.tablefile'),
        ),
    ]
