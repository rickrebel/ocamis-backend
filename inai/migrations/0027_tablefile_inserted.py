# Generated by Django 4.1.6 on 2023-05-19 16:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inai', '0026_alter_entityweek_year_month'),
    ]

    operations = [
        migrations.AddField(
            model_name='tablefile',
            name='inserted',
            field=models.BooleanField(default=False),
        ),
    ]
