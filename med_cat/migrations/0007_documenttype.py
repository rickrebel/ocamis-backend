# Generated by Django 4.1.6 on 2024-06-10 17:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('med_cat', '0006_rename_entity_area_provider_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentType',
            fields=[
                ('name', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('is_aggregate', models.BooleanField(blank=True, default=False, null=True)),
                ('aggregate_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='med_cat.documenttype')),
            ],
            options={
                'verbose_name': 'Tipo de Documento',
                'verbose_name_plural': 'Tipos de Documento',
            },
        ),
    ]
