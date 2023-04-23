# Generated by Django 4.1.6 on 2023-04-23 05:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='StatusTask',
            fields=[
                ('name', models.CharField(max_length=80, primary_key=True, serialize=False)),
                ('public_name', models.CharField(blank=True, max_length=120, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('order', models.IntegerField(default=5)),
                ('icon', models.CharField(blank=True, max_length=30, null=True)),
                ('color', models.CharField(blank=True, max_length=30, null=True)),
                ('is_completed', models.BooleanField(default=False)),
                ('macro_status', models.CharField(blank=True, default='in_progress', max_length=30, null=True)),
            ],
            options={
                'verbose_name': 'Status de tarea',
                'verbose_name_plural': '3. Status de tareas',
                'db_table': 'classify_task_statustask',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='TaskFunction',
            fields=[
                ('name', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('model_name', models.CharField(blank=True, choices=[('petition', 'Solicitud (Petición)'), ('file_control', 'Grupo de Control'), ('data_file', 'DataFile (archivo de datos)'), ('reply_file', 'ReplyFile (.zip)'), ('sheet_file', 'Pestaña')], max_length=100, null=True)),
                ('public_name', models.CharField(blank=True, max_length=120, null=True)),
                ('is_active', models.BooleanField(default=False)),
                ('is_from_aws', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Función (tarea)',
                'verbose_name_plural': '2. Funciones (tareas)',
                'ordering': ['-is_active', 'model_name', 'is_from_aws', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Stage',
            fields=[
                ('name', models.CharField(max_length=80, primary_key=True, serialize=False)),
                ('public_name', models.CharField(max_length=120)),
                ('action_text', models.CharField(blank=True, max_length=120, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('order', models.IntegerField(default=5)),
                ('icon', models.CharField(blank=True, max_length=30, null=True)),
                ('available_next_stages', models.ManyToManyField(blank=True, related_name='previous_stages', to='classify_task.stage')),
                ('main_function', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stages', to='classify_task.taskfunction', verbose_name='Función principal')),
                ('next_stage', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='previous_stage', to='classify_task.stage')),
                ('re_process_stages', models.ManyToManyField(blank=True, related_name='re_processing', to='classify_task.stage', verbose_name='Etapas a re-procesar')),
            ],
            options={
                'verbose_name': 'Etapa',
                'verbose_name_plural': '4. Etapas',
                'ordering': ['order'],
            },
        ),
    ]
