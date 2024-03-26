# Generated by Django 4.1.6 on 2024-03-26 21:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classify_task', '0017_userprofile_is_manager'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stage',
            name='stage_group',
            field=models.CharField(blank=True, choices=[('transformation', 'Transformación'), ('months', 'Meses'), ('provider', 'Proveedor'), ('provider-petition', 'Proveedor (Solicitud)'), ('provider-control', 'Proveedor (Grupos de control)'), ('provider-month', 'Proveedor (Meses)')], max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='taskfunction',
            name='group_queue',
            field=models.CharField(blank=True, choices=[('petition', 'Solicitud (Petición)'), ('file_control', 'Grupo de Control'), ('data_file', 'DataFile (archivo de datos)'), ('reply_file', 'ReplyFile (.zip)'), ('sheet_file', 'Pestaña'), ('entity_week', 'Semana Proveedor'), ('entity_month', 'Mes Proveedor'), ('provider', 'Proveedor')], max_length=100, null=True, verbose_name='agrupables'),
        ),
        migrations.AlterField(
            model_name='taskfunction',
            name='model_name',
            field=models.CharField(blank=True, choices=[('petition', 'Solicitud (Petición)'), ('file_control', 'Grupo de Control'), ('data_file', 'DataFile (archivo de datos)'), ('reply_file', 'ReplyFile (.zip)'), ('sheet_file', 'Pestaña'), ('entity_week', 'Semana Proveedor'), ('entity_month', 'Mes Proveedor'), ('provider', 'Proveedor')], max_length=100, null=True),
        ),
    ]
