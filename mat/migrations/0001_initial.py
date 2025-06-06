# Generated by Django 4.1.13 on 2024-07-16 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MotherDrug',
            fields=[
                ('key', models.CharField(db_column='key', max_length=255, primary_key=True, serialize=False)),
                ('prescribed_total', models.IntegerField(db_column='prescribed')),
                ('delivered_total', models.IntegerField(db_column='delivered')),
                ('total', models.IntegerField(db_column='total')),
            ],
            options={
                'verbose_name': 'Tabla Madre. Drugs',
                'verbose_name_plural': 'Tabla Madre. Drugs',
                'db_table': 'mother_drug',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='MotherDrugEntity',
            fields=[
                ('iso_year', models.PositiveSmallIntegerField(db_column='iso_year', primary_key=True, serialize=False)),
                ('iso_week', models.PositiveSmallIntegerField(db_column='iso_week')),
                ('year', models.PositiveSmallIntegerField(db_column='year')),
                ('month', models.PositiveSmallIntegerField(db_column='month')),
                ('prescribed_total', models.IntegerField(db_column='prescribed')),
                ('delivered_total', models.IntegerField(db_column='delivered')),
                ('total', models.IntegerField(db_column='total')),
            ],
            options={
                'verbose_name': 'Entidad de Medicamentos',
                'verbose_name_plural': 'Entidades de Medicamentos',
                'db_table': 'mat_drug_entity',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='MotherDrugPriority',
            fields=[
                ('key', models.CharField(db_column='key', max_length=255, primary_key=True, serialize=False)),
                ('prescribed_total', models.IntegerField(db_column='prescribed')),
                ('delivered_total', models.IntegerField(db_column='delivered')),
                ('total', models.IntegerField(db_column='total')),
            ],
            options={
                'verbose_name': 'Dato Prioridad',
                'verbose_name_plural': 'Datos Prioridad',
                'db_table': 'mother_drug_priority',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='MotherDrugTotals',
            fields=[
                ('prescribed_total', models.IntegerField(db_column='prescribed')),
                ('delivered_total', models.IntegerField(db_column='delivered')),
                ('total', models.IntegerField(db_column='total', primary_key=True, serialize=False)),
            ],
            options={
                'verbose_name': 'Dato Total',
                'verbose_name_plural': 'Datos Totales',
                'db_table': 'mother_drug_totals',
                'managed': False,
            },
        ),
    ]
