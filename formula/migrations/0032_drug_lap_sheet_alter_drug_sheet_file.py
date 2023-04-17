# Generated by Django 4.1.6 on 2023-04-17 18:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inai', '0078_remove_sheetfile_valid_insert_lapsheet_valid_insert_and_more'),
        ('formula', '0031_alter_prescription_medical_unit'),
    ]

    operations = [
        migrations.AddField(
            model_name='drug',
            name='lap_sheet',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='inai.lapsheet'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='drug',
            name='sheet_file',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='inai.sheetfile'),
            preserve_default=False,
        ),
    ]
