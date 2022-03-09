# Generated by Django 2.2.25 on 2022-03-09 01:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('report', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='clues',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalog.CLUES'),
        ),
        migrations.AlterField(
            model_name='report',
            name='institution',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalog.Institution', verbose_name='Institución'),
        ),
        migrations.AlterField(
            model_name='report',
            name='state',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalog.State', verbose_name='Entidad'),
        ),
        migrations.AlterField(
            model_name='responsable',
            name='clues',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='responsables', to='catalog.CLUES'),
        ),
        migrations.AlterField(
            model_name='responsable',
            name='institution',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='responsables', to='catalog.Institution'),
        ),
        migrations.AlterField(
            model_name='responsable',
            name='state',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='responsables', to='catalog.State'),
        ),
        migrations.AlterField(
            model_name='supply',
            name='component',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='medicine.Component'),
        ),
        migrations.AlterField(
            model_name='supply',
            name='disease',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='report.Disease', verbose_name='Padecimiento'),
        ),
        migrations.AlterField(
            model_name='supply',
            name='presentation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='medicine.Presentation'),
        ),
        migrations.AlterField(
            model_name='supply',
            name='report',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supplies', to='report.Report'),
        ),
        migrations.AlterField(
            model_name='testimonymedia',
            name='report',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='testimonies_media', to='report.Report'),
        ),
    ]
