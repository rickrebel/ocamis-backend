# Generated by Django 4.1.6 on 2023-04-08 01:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0039_area_hex_hash'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='agency',
            table='catalog_agency',
        ),
        migrations.AlterModelTable(
            name='area',
            table='catalog_area',
        ),
        migrations.AlterModelTable(
            name='delegation',
            table='catalog_delegation',
        ),
        migrations.AlterModelTable(
            name='jurisdiction',
            table='catalog_jurisdiction',
        ),
        migrations.AlterModelTable(
            name='typology',
            table='catalog_typology',
        ),
    ]
