# Generated by Django 4.1.6 on 2024-03-27 03:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0018_rename_entity_agency_provider_and_more'),
        ('inai', '0072_rename_entity_months_petition_month_records_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='petition',
            name='template_text',
            field=models.TextField(blank=True, null=True, verbose_name='Texto para la plantilla'),
        ),
        migrations.AlterField(
            model_name='variable',
            name='variable_type',
            field=models.CharField(choices=[('string', 'String'), ('provider', 'By Provider'), ('date', 'Date')], default='string', max_length=10),
        ),
        migrations.CreateModel(
            name='VariableValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=255)),
                ('petition', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='variable_values', to='inai.petition')),
                ('provider', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='variable_values', to='geo.provider')),
                ('variable', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='values', to='inai.variable')),
            ],
            options={
                'verbose_name': 'Valor de variable',
                'verbose_name_plural': 'Valores de variable',
            },
        ),
    ]
