# Generated by Django 4.1.6 on 2023-02-27 21:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_param', '0021_rename_requiered_finalfield_required_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='finalfield',
            name='is_unique',
            field=models.BooleanField(default=False, help_text='Puede ser una llave única', verbose_name='Único'),
        ),
    ]
