# Generated by Django 4.1.6 on 2023-05-19 20:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classify_task', '0002_alter_taskfunction_model_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='taskfunction',
            options={'ordering': ['-is_active', 'model_name', '-is_from_aws', 'name'], 'verbose_name': 'Función (tarea)', 'verbose_name_plural': '2. Funciones (tareas)'},
        ),
        migrations.AlterField(
            model_name='taskfunction',
            name='model_name',
            field=models.CharField(blank=True, choices=[('petition', 'Solicitud (Petición)'), ('file_control', 'Grupo de Control'), ('data_file', 'DataFile (archivo de datos)'), ('reply_file', 'ReplyFile (.zip)'), ('sheet_file', 'Pestaña'), ('entity_week', 'Semana Proveedor'), ('entity_month', 'Mes Proveedor'), ('entity', 'Proveedor')], max_length=100, null=True),
        ),
    ]
