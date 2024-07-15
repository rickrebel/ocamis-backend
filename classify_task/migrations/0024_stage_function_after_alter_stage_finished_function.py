# Generated by Django 4.1.6 on 2024-07-14 03:39

from django.db import migrations, models


def add_function_after(apps, schema_editor):
    Stage = apps.get_model('classify_task', 'Stage')
    # RICK TASK: Verificar este tema
    new_functions = [
        ('explore', 'build_sample_data_after'),
        ('cluster', 'find_coincidences_from_aws'),
    ]
    # explore_stage = Stage.objects.get(name='explore')
    # explore_stage.function_after = 'explore_after'
    # explore_stage.save()
    for stage_name, function_name in new_functions:
        stage = Stage.objects.get(name=stage_name)
        stage.function_after = function_name
        stage.save()


class Migration(migrations.Migration):

    dependencies = [
        ('classify_task', '0023_alter_taskfunction_group_queue_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='stage',
            name='function_after',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Función llegando de Lambda'),
        ),
        migrations.AlterField(
            model_name='stage',
            name='finished_function',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Función al terminar hijos'),
        ),
        migrations.RunPython(add_function_after),
    ]
