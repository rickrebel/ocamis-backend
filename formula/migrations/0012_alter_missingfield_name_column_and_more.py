# Generated by Django 4.1.6 on 2023-03-02 07:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data_param', '0025_alter_filecontrol_data_group_and_more'),
        ('formula', '0011_alter_missingfield_name_column'),
    ]

    operations = [
        migrations.AlterField(
            model_name='missingfield',
            name='name_column',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_param.namecolumn'),
        ),
        migrations.AlterField(
            model_name='prescription',
            name='document_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='formula.documenttype'),
        ),
    ]
