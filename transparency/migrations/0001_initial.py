# Generated by Django 4.1.6 on 2023-03-02 06:35

from django.db import migrations, models
import django.db.models.deletion
import transparency.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('category', '0029_delete_transparencyindex_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Anomaly',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_name', models.CharField(max_length=255, verbose_name='Nombre público')),
                ('name', models.CharField(max_length=25, verbose_name='Nombre (devs)')),
                ('is_public', models.BooleanField(default=True)),
                ('description', models.TextField(blank=True, null=True, verbose_name='Descripción')),
                ('icon', models.CharField(blank=True, max_length=20, null=True)),
                ('is_calculated', models.BooleanField(default=False)),
                ('order', models.IntegerField(default=5)),
                ('color', models.CharField(blank=True, max_length=30, null=True, verbose_name='Color')),
            ],
            options={
                'verbose_name': 'Anomalía en los datos',
                'verbose_name_plural': 'Anomalías en los datos',
                'db_table': 'category_anomaly',
            },
        ),
        migrations.CreateModel(
            name='TransparencyIndex',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=20)),
                ('public_name', models.CharField(max_length=80)),
                ('description', models.TextField(blank=True, null=True)),
                ('scheme_color', models.CharField(blank=True, max_length=90, null=True, verbose_name='Esquema de color')),
                ('viz_params', models.JSONField(blank=True, default=transparency.models.default_dict)),
                ('order_viz', models.IntegerField(default=-3, verbose_name='Orden en visualización')),
            ],
            options={
                'verbose_name': 'Transparencia: Indicador',
                'verbose_name_plural': 'Transparencia: Indicadores',
                'ordering': ['order_viz'],
                'db_table': 'category_transparencyindex',
            },
        ),
        migrations.CreateModel(
            name='TransparencyLevel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transparency_index', models.IntegerField(blank=True, null=True)),
                ('short_name', models.CharField(max_length=20)),
                ('public_name', models.CharField(max_length=80)),
                ('value', models.IntegerField(default=0, help_text='Para ordenar y decidier según menor')),
                ('description', models.TextField(blank=True, null=True)),
                ('other_conditions', models.JSONField(blank=True, default=transparency.models.default_list)),
                ('viz_params', models.JSONField(blank=True, default=transparency.models.default_dict)),
                ('is_default', models.BooleanField(default=False)),
                ('color', models.CharField(blank=True, max_length=20, null=True)),
                ('order_viz', models.IntegerField(default=-3, verbose_name='Orden en visualización')),
                ('value_ctrls', models.IntegerField(default=-3, verbose_name='Priorización entre controles')),
                ('value_pets', models.IntegerField(default=-3, verbose_name='Priorización entre solicitudes')),
                ('anomalies', models.ManyToManyField(blank=True, to='transparency.anomaly', verbose_name='Anomalías relacionadas')),
                ('file_formats', models.ManyToManyField(blank=True, to='category.fileformat', verbose_name='Formatos de archivo')),
                ('final_level', models.ForeignKey(blank=True, help_text='Si existe, se va a ese nivel de indicador principal', null=True, on_delete=django.db.models.deletion.CASCADE, to='transparency.transparencylevel', verbose_name='Concentrado destino')),
            ],
            options={
                'verbose_name': 'Transparencia: Nivel',
                'verbose_name_plural': 'Transparencia: Niveles',
                'db_table': 'category_transparencylevel',
            },
        ),
    ]
