# Generated by Django 4.1.13 on 2024-10-31 09:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0003_institution_alternative_codes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clues',
            name='admin_institution',
            field=models.CharField(max_length=120, verbose_name='NOMBRE DE LA INS ADM'),
        ),
    ]
