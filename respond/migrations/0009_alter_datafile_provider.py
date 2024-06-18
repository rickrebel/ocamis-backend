# Generated by Django 4.1.6 on 2024-06-17 18:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0023_rename_status_operative_provider_status_priority'),
        ('respond', '0008_remove_datafile_file_control_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datafile',
            name='provider',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='data_files', to='geo.provider'),
        ),
    ]
