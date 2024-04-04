# Generated by Django 4.1.6 on 2024-04-03 23:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0018_rename_entity_agency_provider_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='provider',
            options={'ordering': ['state__name'], 'verbose_name': 'Proveedor', 'verbose_name_plural': 'Proveedores'},
        ),
        migrations.AddField(
            model_name='provider',
            name='variables',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
