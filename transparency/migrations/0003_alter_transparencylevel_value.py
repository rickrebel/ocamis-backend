# Generated by Django 4.1.6 on 2024-07-14 19:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transparency', '0002_alter_anomaly_table_alter_transparencyindex_table_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transparencylevel',
            name='value',
            field=models.IntegerField(default=0, help_text='Para ordenar y decidir según menor'),
        ),
    ]
