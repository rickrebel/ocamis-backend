# Generated by Django 2.2.25 on 2022-08-08 16:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inai', '0016_auto_20220802_0751'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='datafile',
            options={'ordering': ['file'], 'verbose_name': 'Archivo con datos', 'verbose_name_plural': 'Archivos con datos'},
        ),
        migrations.AlterField(
            model_name='petitionnegativereason',
            name='petition',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='negative_reasons', to='inai.Petition'),
        ),
    ]
