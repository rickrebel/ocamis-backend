# Generated by Django 4.1.6 on 2024-03-26 20:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('report', '0002_alter_supply_options_alter_report_medication_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='covidreport',
            name='municipality',
        ),
        migrations.RemoveField(
            model_name='covidreport',
            name='persona',
        ),
        migrations.RemoveField(
            model_name='covidreport',
            name='state',
        ),
        migrations.RemoveField(
            model_name='dosiscovid',
            name='covid_report',
        ),
        migrations.RemoveField(
            model_name='dosiscovid',
            name='municipality',
        ),
        migrations.RemoveField(
            model_name='dosiscovid',
            name='state',
        ),
        migrations.RemoveField(
            model_name='report',
            name='clues',
        ),
        migrations.RemoveField(
            model_name='report',
            name='institution',
        ),
        migrations.RemoveField(
            model_name='report',
            name='persona',
        ),
        migrations.RemoveField(
            model_name='report',
            name='state',
        ),
        migrations.RemoveField(
            model_name='responsable',
            name='clues',
        ),
        migrations.RemoveField(
            model_name='responsable',
            name='institution',
        ),
        migrations.RemoveField(
            model_name='responsable',
            name='state',
        ),
        migrations.RemoveField(
            model_name='supply',
            name='component',
        ),
        migrations.RemoveField(
            model_name='supply',
            name='disease',
        ),
        migrations.RemoveField(
            model_name='supply',
            name='presentation',
        ),
        migrations.RemoveField(
            model_name='supply',
            name='report',
        ),
        migrations.RemoveField(
            model_name='testimonymedia',
            name='report',
        ),
        migrations.DeleteModel(
            name='ComplementReport',
        ),
        migrations.DeleteModel(
            name='CovidReport',
        ),
        migrations.DeleteModel(
            name='DosisCovid',
        ),
        migrations.DeleteModel(
            name='Persona',
        ),
        migrations.DeleteModel(
            name='Report',
        ),
        migrations.DeleteModel(
            name='Responsable',
        ),
        migrations.DeleteModel(
            name='Supply',
        ),
        migrations.DeleteModel(
            name='TestimonyMedia',
        ),
    ]
