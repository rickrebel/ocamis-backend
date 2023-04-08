# Generated by Django 4.1.6 on 2023-04-08 02:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('formula', '0023_remove_diagnosis_aggregate_to_and_more'),
        ('med_cat', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prescription',
            name='area',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='med_cat.area'),
        ),
        migrations.AlterField(
            model_name='prescription',
            name='diagnosis',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='med_cat.diagnosis'),
        ),
        migrations.AlterField(
            model_name='prescription',
            name='doctor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='med_cat.doctor'),
        ),
        migrations.DeleteModel(
            name='Diagnosis',
        ),
        migrations.DeleteModel(
            name='Doctor',
        ),
    ]
