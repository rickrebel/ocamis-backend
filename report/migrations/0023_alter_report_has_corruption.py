# Generated by Django 4.1.5 on 2023-01-24 22:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('report', '0022_alter_complementreport_public_testimony_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='has_corruption',
            field=models.BooleanField(blank=True, null=True, verbose_name='¿Incluyó corrupción?'),
        ),
    ]
