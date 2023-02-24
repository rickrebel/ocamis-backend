# Generated by Django 4.1.6 on 2023-02-24 09:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('formula', '0004_alter_missingfield_errors_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='doctor',
            name='especialidad_medico',
        ),
        migrations.RemoveField(
            model_name='doctor',
            name='institution',
        ),
        migrations.RemoveField(
            model_name='droug',
            name='container',
        ),
        migrations.RemoveField(
            model_name='droug',
            name='data_file',
        ),
        migrations.RemoveField(
            model_name='droug',
            name='delivered',
        ),
        migrations.RemoveField(
            model_name='droug',
            name='recipe_prescr',
        ),
        migrations.RemoveField(
            model_name='missingfield',
            name='missing_row',
        ),
        migrations.RemoveField(
            model_name='missingfield',
            name='name_column',
        ),
        migrations.RemoveField(
            model_name='missingrow',
            name='droug',
        ),
        migrations.RemoveField(
            model_name='missingrow',
            name='file',
        ),
        migrations.RemoveField(
            model_name='missingrow',
            name='prescription',
        ),
        migrations.RemoveField(
            model_name='prescription',
            name='clues',
        ),
        migrations.RemoveField(
            model_name='prescription',
            name='delegacion',
        ),
        migrations.RemoveField(
            model_name='prescription',
            name='delivered',
        ),
        migrations.RemoveField(
            model_name='prescription',
            name='doctor',
        ),
        migrations.RemoveField(
            model_name='prescription',
            name='type_document',
        ),
        migrations.DeleteModel(
            name='Delivered',
        ),
        migrations.DeleteModel(
            name='Doctor',
        ),
        migrations.DeleteModel(
            name='DocumentType',
        ),
        migrations.DeleteModel(
            name='Droug',
        ),
        migrations.DeleteModel(
            name='MedicalSpeciality',
        ),
        migrations.DeleteModel(
            name='MissingField',
        ),
        migrations.DeleteModel(
            name='MissingRow',
        ),
        migrations.DeleteModel(
            name='Prescription',
        ),
    ]
