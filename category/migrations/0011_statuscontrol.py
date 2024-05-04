# Generated by Django 4.1.6 on 2024-05-02 20:46

from django.db import migrations, models


def copy_old_status_control(apps, schema_editor):
    OldStatusControl = apps.get_model("category", "OldStatusControl")
    StatusControl = apps.get_model("category", "StatusControl")
    for old_status in OldStatusControl.objects.all():
        StatusControl.objects.create(
            name=old_status.name,
            group=old_status.group,
            public_name=old_status.public_name,
            color=old_status.color,
            icon=old_status.icon,
            order=old_status.order,
            description=old_status.description,
            addl_params=old_status.addl_params,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0010_alter_oldstatuscontrol_table'),
    ]

    operations = [
        migrations.CreateModel(
            name='StatusControl',
            fields=[
                ('name', models.CharField(max_length=120, primary_key=True, serialize=False)),
                ('group', models.CharField(choices=[('petition', 'de Solicitud'), ('data', 'Datos entregados'), ('complain', 'Quejas - Revisiones'), ('register', 'Registro de variables'), ('provider', 'para Proveedores'), ('priority', 'Prioridad en Solicitudes'), ('process', 'Procesamiento de archivos (solo devs)')], default='petition', max_length=10, verbose_name='grupo de status')),
                ('public_name', models.CharField(max_length=255)),
                ('color', models.CharField(blank=True, help_text='https://vuetifyjs.com/en/styles/colors/', max_length=30, null=True)),
                ('icon', models.CharField(blank=True, max_length=40, null=True)),
                ('order', models.IntegerField(default=4)),
                ('description', models.TextField(blank=True, null=True)),
                ('addl_params', models.JSONField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Status de control',
                'verbose_name_plural': 'Status de control',
                'ordering': ['group', 'order'],
            },
        ),
        migrations.RunPython(copy_old_status_control),
    ]
