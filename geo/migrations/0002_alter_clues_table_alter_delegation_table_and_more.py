# Generated by Django 4.1.6 on 2023-04-27 20:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='clues',
            table='geo_clues',
        ),
        migrations.AlterModelTable(
            name='delegation',
            table='geo_delegation',
        ),
        migrations.AlterModelTable(
            name='institution',
            table='geo_institution',
        ),
        migrations.AlterModelTable(
            name='jurisdiction',
            table='geo_jurisdiction',
        ),
        migrations.AlterModelTable(
            name='municipality',
            table='geo_municipality',
        ),
        migrations.AlterModelTable(
            name='typology',
            table='geo_typology',
        ),
    ]
