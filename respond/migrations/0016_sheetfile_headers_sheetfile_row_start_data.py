# Generated by Django 4.1.6 on 2024-07-16 02:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('respond', '0015_alter_sheetfile_file_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='sheetfile',
            name='headers',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sheetfile',
            name='row_start_data',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
