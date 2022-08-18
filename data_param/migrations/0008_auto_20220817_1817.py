# Generated by Django 2.2.25 on 2022-08-17 23:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_param', '0007_auto_20220816_1319'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='finalfield',
            options={'ordering': ['-is_common', 'verbose_name'], 'verbose_name': 'Campo final', 'verbose_name_plural': 'Campos finales (en DB)'},
        ),
        migrations.AddField(
            model_name='datagroup',
            name='color',
            field=models.CharField(default='lime', max_length=20),
        ),
        migrations.AlterField(
            model_name='finalfield',
            name='verbose_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Nombre público'),
        ),
    ]
