# Generated by Django 4.1.6 on 2023-05-19 16:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classify_task', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taskfunction',
            name='model_name',
            field=models.CharField(blank=True, choices=[('petition', 'Solicitud (Petición)'), ('file_control', 'Grupo de Control'), ('data_file', 'DataFile (archivo de datos)'), ('reply_file', 'ReplyFile (.zip)'), ('sheet_file', 'Pestaña'), ('entity_week', 'Semana Proveedor')], max_length=100, null=True),
        ),
    ]
