# Generated by Django 4.1.6 on 2024-08-14 07:51

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('rds', '0003_rename_comment_operation_notes_and_more'),
        ('med_cat', '0001_initial'),
        ('inai', '0003_alter_monthrecord_cluster'),
        ('formula', '0002_matdrugtotals2'),
    ]

    operations = [
        migrations.CreateModel(
            name='MatDrugEntity2',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('prescribed_total', models.IntegerField()),
                ('delivered_total', models.IntegerField()),
                ('total', models.IntegerField()),
                ('cluster', models.ForeignKey(default='first', on_delete=django.db.models.deletion.DO_NOTHING, to='rds.cluster')),
                ('delivered', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='med_cat.delivered')),
                ('medicament', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='med_cat.medicament')),
                ('week_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inai.weekrecord')),
            ],
            options={
                'db_table': 'mat_drug_entity2',
            },
        ),
    ]
