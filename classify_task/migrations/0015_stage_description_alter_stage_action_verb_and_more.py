# Generated by Django 4.1.6 on 2023-10-30 17:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classify_task', '0014_rename_description_stage_action_verb'),
    ]

    operations = [
        migrations.AddField(
            model_name='stage',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='stage',
            name='action_verb',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='stage',
            name='stage_group',
            field=models.CharField(blank=True, choices=[('transformation', 'Transformación'), ('months', 'Meses'), ('entity', 'Proveedor'), ('entity-petition', 'Proveedor (petición)'), ('entity-control', 'Proveedor (Grupos de control)'), ('entity-month', 'Proveedor (Meses)')], max_length=30, null=True),
        ),
    ]
