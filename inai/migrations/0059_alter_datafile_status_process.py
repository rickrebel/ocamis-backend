# Generated by Django 4.1.6 on 2023-03-22 03:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0032_remove_filetype_id_alter_filetype_name'),
        ('inai', '0058_remove_datafile_sheets_info_datafile_filtered_sheets_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datafile',
            name='status_process',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='category.statuscontrol'),
        ),
    ]
