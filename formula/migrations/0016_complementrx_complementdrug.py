# Generated by Django 4.1.6 on 2023-10-08 23:40

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('med_cat', '0003_delivered_alternative_names'),
        ('formula', '0015_alter_matdrugpriority_clues_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ComplementRx',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('age', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('record', models.CharField(blank=True, max_length=255, null=True, verbose_name='Expediente')),
                ('personal_number', models.CharField(blank=True, max_length=80, null=True, verbose_name='Número personal')),
                ('gender', models.CharField(blank=True, max_length=30, null=True, verbose_name='Género')),
                ('area', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='med_cat.area')),
                ('diagnosis', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='med_cat.diagnosis')),
                ('rx', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='complements', to='formula.rx')),
            ],
            options={
                'verbose_name': 'Complemento de Receta',
                'verbose_name_plural': 'Complementos de Receta',
            },
        ),
        migrations.CreateModel(
            name='ComplementDrug',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('lote', models.CharField(blank=True, max_length=80, null=True, verbose_name='Lote')),
                ('expiration_date', models.DateField(blank=True, null=True, verbose_name='Fecha de caducidad')),
                ('total_price', models.FloatField(blank=True, null=True)),
                ('drug', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='complements', to='formula.drug')),
            ],
            options={
                'verbose_name': 'Insumos',
                'verbose_name_plural': 'Insumos (medicamentos)',
            },
        ),
    ]
