# Generated by Django 4.1.6 on 2024-12-16 17:21

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('med_cat', '0003_alter_doctor_professional_license'),
        ('inai', '0005_weekrecord_self_repeated_count'),
        ('formula', '0003_matdrugentity2'),
    ]

    operations = [
        migrations.CreateModel(
            name='ViewDrugEntity2',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('year', models.PositiveSmallIntegerField()),
                ('month', models.PositiveSmallIntegerField()),
                ('year_week', models.CharField(max_length=10)),
                ('iso_week', models.PositiveSmallIntegerField()),
                ('iso_year', models.PositiveSmallIntegerField()),
                ('prescribed_total', models.IntegerField()),
                ('delivered_total', models.IntegerField()),
                ('total', models.IntegerField()),
            ],
            options={
                'db_table': 'view_drug_entity2',
                'managed': False,
            },
        ),
        migrations.AlterField(
            model_name='matdrugentity2',
            name='delivered',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='med_cat.delivered'),
        ),
        migrations.AlterField(
            model_name='matdrugentity2',
            name='medicament',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='med_cat.medicament'),
        ),
        migrations.AlterField(
            model_name='matdrugentity2',
            name='week_record',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='inai.weekrecord'),
        ),
    ]
