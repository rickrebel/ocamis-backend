# Generated by Django 4.1.6 on 2023-02-11 23:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

import data_param.models
import inai.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('category', '0025_statustask'),
        ('inai', '0041_alter_datafile_all_results_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='datafile',
            name='sheet_names',
            field=models.JSONField(blank=True, null=True, verbose_name='Nombres de las hojas'),
        ),
        migrations.AlterField(
            model_name='datafile',
            name='explore_data',
            field=models.JSONField(blank=True, null=True, verbose_name='Primeros datos, de exploración'),
        ),
        migrations.AlterField(
            model_name='filecontrol',
            name='addl_params',
            field=models.JSONField(default=data_param.models.default_addl_params),
        ),
        migrations.AlterField(
            model_name='transformation',
            name='addl_params',
            field=models.JSONField(blank=True, default=data_param.models.default_params, null=True),
        ),
        migrations.CreateModel(
            name='AsyncTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_id', models.CharField(blank=True, max_length=100, null=True)),
                ('function_name', models.CharField(blank=True, max_length=100, null=True, verbose_name='Nombre de la función')),
                ('function_after', models.CharField(blank=True, max_length=100, null=True)),
                ('original_request', models.JSONField(blank=True, null=True, verbose_name='Request original')),
                ('params_after', models.JSONField(blank=True, null=True, verbose_name='Parámetros de la función after')),
                ('result', models.JSONField(blank=True, null=True)),
                ('error', models.TextField(blank=True, null=True)),
                ('traceback', models.TextField(blank=True, null=True)),
                ('date_start', models.DateTimeField(blank=True, null=True)),
                ('date_end', models.DateTimeField(blank=True, null=True)),
                ('data_file', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='async_tasks', to='inai.datafile')),
                ('file_control', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='async_tasks', to='inai.filecontrol')),
                ('parent_task', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='child_tasks', to='inai.asynctask')),
                ('petition', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='async_tasks', to='inai.petition')),
                ('process_file', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='async_tasks', to='inai.processfile')),
                ('status_task', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='category.statustask', verbose_name='Estado de la tarea')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Tarea asincrónica',
                'verbose_name_plural': 'Tareas asincrónicas',
                'ordering': ['-date_start'],
            },
        ),
    ]
