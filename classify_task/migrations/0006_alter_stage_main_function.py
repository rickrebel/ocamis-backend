# Generated by Django 4.1.6 on 2023-03-23 19:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('classify_task', '0005_rename_retry_function_stage_main_function_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stage',
            name='main_function',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='classify_task.taskfunction', verbose_name='Función principal'),
        ),
    ]
