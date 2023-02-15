# Generated by Django 4.1.6 on 2023-02-15 03:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inai', '0042_datafile_sheet_names_alter_datafile_explore_data_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='datafile',
            name='suffix',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='asynctask',
            name='function_after',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Función a ejecutar después'),
        ),
    ]
