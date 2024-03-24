# Generated by Django 4.1.6 on 2024-03-24 01:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('respond', '0001_initial'),
        ('task', '0017_alter_offlinetask_activity_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asynctask',
            name='data_file',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='async_tasks', to='respond.datafile'),
        ),
        migrations.AlterField(
            model_name='asynctask',
            name='reply_file',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='async_tasks', to='respond.replyfile'),
        ),
        migrations.AlterField(
            model_name='asynctask',
            name='sheet_file',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='async_tasks', to='respond.sheetfile'),
        ),
        migrations.AlterField(
            model_name='filepath',
            name='data_file',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='respond.datafile'),
        ),
        migrations.AlterField(
            model_name='filepath',
            name='reply_file',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='file_paths', to='respond.replyfile'),
        ),
        migrations.AlterField(
            model_name='filepath',
            name='sheet_file',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='respond.sheetfile'),
        ),
        migrations.AlterField(
            model_name='filepath',
            name='table_file',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='respond.tablefile'),
        ),
    ]
