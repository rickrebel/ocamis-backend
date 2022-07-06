# Generated by Django 2.2.25 on 2022-03-19 18:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('report', '0006_auto_20220313_1857'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='covidreport',
            options={'verbose_name': 'Reporte COVID', 'verbose_name_plural': '3. Reportes COVID'},
        ),
        migrations.AlterModelOptions(
            name='dosiscovid',
            options={'verbose_name': 'Dosis', 'verbose_name_plural': '5. Dosis aplicadas y negadas'},
        ),
        migrations.AlterModelOptions(
            name='persona',
            options={'verbose_name': 'Persona Reportante', 'verbose_name_plural': '4. Personas Reportantes'},
        ),
        migrations.AlterModelOptions(
            name='report',
            options={'verbose_name': 'Reporte', 'verbose_name_plural': '1. Reportes'},
        ),
        migrations.AlterModelOptions(
            name='responsable',
            options={'verbose_name': 'Responsable', 'verbose_name_plural': '6. Responsables'},
        ),
        migrations.AlterModelOptions(
            name='supply',
            options={'verbose_name': 'Medicamento o insumo', 'verbose_name_plural': '2. Medicamentos/Insumos de reportes'},
        ),
        migrations.AlterModelOptions(
            name='testimonymedia',
            options={'verbose_name': 'Archivo de testimonio', 'verbose_name_plural': '8. Archivos de testimonio'},
        ),
        migrations.CreateModel(
            name='ComplementReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=30)),
                ('testimony', models.TextField(blank=True, null=True)),
                ('public_testimony', models.NullBooleanField()),
                ('validated', models.NullBooleanField(default=None)),
                ('validator', models.IntegerField(blank=True, null=True)),
                ('validated_date', models.DateTimeField(blank=True, null=True)),
                ('pending', models.BooleanField(default=False)),
                ('session_ga', models.CharField(blank=True, max_length=255, null=True)),
                ('has_corruption', models.NullBooleanField(verbose_name='¿Incluyó corrupción?')),
                ('narration', models.TextField(blank=True, null=True, verbose_name='Relato de la corrupción')),
                ('origin_app', models.CharField(default='CD2', max_length=100, verbose_name='Aplicación')),
                ('covid_report', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='report.CovidReport')),
                ('report', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='report.Report')),
            ],
        ),
    ]
