# Generated by Django 4.1.6 on 2024-07-02 17:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0023_rename_status_operative_provider_status_priority'),
    ]

    operations = [
        migrations.AddField(
            model_name='provider',
            name='strategy',
            field=models.TextField(blank=True, null=True, verbose_name='Estrategia para solicitudes'),
        ),
        migrations.AlterField(
            model_name='agency',
            name='nombreSujetoObligado',
            field=models.CharField(blank=True, help_text='nombreSujetoObligado del INAI', max_length=160, null=True, verbose_name='nombreSujetoObligado'),
        ),
    ]
