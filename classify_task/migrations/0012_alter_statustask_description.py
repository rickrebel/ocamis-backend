# Generated by Django 4.1.6 on 2023-10-30 16:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classify_task', '0011_stage_stage_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='statustask',
            name='description',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Descripción'),
        ),
    ]
