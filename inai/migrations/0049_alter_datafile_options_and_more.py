# Generated by Django 4.1.6 on 2023-07-26 23:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inai', '0048_alter_behavior_options_alter_entitymonth_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='datafile',
            options={'ordering': ['-id'], 'verbose_name': 'Archivo con datos', 'verbose_name_plural': '3. Archivos entregados con datos'},
        ),
        migrations.RenameField(
            model_name='entitymonth',
            old_name='last_insertion',
            new_name='last_pre_insertion',
        ),
        migrations.RenameField(
            model_name='entityweek',
            old_name='last_insertion',
            new_name='last_pre_insertion',
        ),
    ]
