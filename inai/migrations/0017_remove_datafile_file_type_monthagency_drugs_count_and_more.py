# Generated by Django 4.1.6 on 2023-05-18 23:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inai', '0016_rename_prescription_count_lapsheet_rx_count_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='datafile',
            name='file_type',
        ),
        migrations.AddField(
            model_name='monthagency',
            name='drugs_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='tablefile',
            name='lap_sheet',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='table_files', to='inai.lapsheet'),
        ),
    ]
