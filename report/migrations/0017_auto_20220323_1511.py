# Generated by Django 2.2.25 on 2022-03-23 21:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('report', '0016_delete_disease'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supply',
            name='disease',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalog.Disease', verbose_name='Padecimiento'),
        ),
    ]
