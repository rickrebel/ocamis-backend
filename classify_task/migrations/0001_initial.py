# Generated by Django 4.1.13 on 2024-07-16 07:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StatusTask',
            fields=[
                ('name', models.CharField(max_length=80, primary_key=True, serialize=False)),
                ('public_name', models.CharField(blank=True, max_length=120, null=True)),
                ('order', models.IntegerField(default=5)),
                ('icon', models.CharField(blank=True, max_length=30, null=True)),
                ('color', models.CharField(blank=True, max_length=30, null=True)),
                ('is_completed', models.BooleanField(default=False)),
                ('macro_status', models.CharField(blank=True, default='in_progress', max_length=30, null=True)),
            ],
            options={
                'verbose_name': 'Status de tarea',
                'verbose_name_plural': '3. Status de tareas',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='TaskFunction',
            fields=[
                ('name', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('lambda_function', models.CharField(blank=True, max_length=100, null=True)),
                ('model_name', models.CharField(blank=True, choices=[('petition', 'Solicitud (Petición)'), ('file_control', 'Grupo de Control'), ('data_file', 'DataFile (archivo de datos)'), ('reply_file', 'ReplyFile (.zip)'), ('sheet_file', 'Hoja (sheet)'), ('week_record', 'Semana Proveedor'), ('month_record', 'Mes Proveedor'), ('provider', 'Proveedor'), ('cluster', 'Cluster'), ('mat_view', 'Materialized View')], max_length=100, null=True)),
                ('public_name', models.CharField(blank=True, max_length=120, null=True)),
                ('is_active', models.BooleanField(default=False, verbose_name='active')),
                ('is_from_aws', models.BooleanField(default=False, verbose_name='AWS')),
                ('is_queueable', models.BooleanField(default=False, verbose_name='queue')),
                ('ebs_percent', models.IntegerField(default=0, verbose_name='% EBS')),
                ('queue_size', models.IntegerField(default=1, verbose_name='queue size')),
                ('group_queue', models.CharField(blank=True, choices=[('petition', 'Solicitud (Petición)'), ('file_control', 'Grupo de Control'), ('data_file', 'DataFile (archivo de datos)'), ('reply_file', 'ReplyFile (.zip)'), ('sheet_file', 'Hoja (sheet)'), ('week_record', 'Semana Proveedor'), ('month_record', 'Mes Proveedor'), ('provider', 'Proveedor'), ('cluster', 'Cluster'), ('mat_view', 'Materialized View')], max_length=100, null=True, verbose_name='agrupables')),
                ('simultaneous_groups', models.IntegerField(default=1, verbose_name='Grupos simultáneos')),
            ],
            options={
                'verbose_name': 'Función (tarea)',
                'verbose_name_plural': '2. Funciones (tareas)',
                'ordering': ['-is_active', 'model_name', '-is_from_aws', 'name'],
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('has_tasks', models.BooleanField(default=False)),
                ('is_manager', models.BooleanField(default=False)),
                ('image', models.ImageField(blank=True, null=True, upload_to='profile_images')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Perfil de usuario',
                'verbose_name_plural': '1. Perfiles de usuario',
            },
        ),
        migrations.CreateModel(
            name='Stage',
            fields=[
                ('name', models.CharField(max_length=80, primary_key=True, serialize=False)),
                ('public_name', models.CharField(max_length=120)),
                ('stage_group', models.CharField(blank=True, choices=[('transformation', 'Transformación'), ('months', 'Meses'), ('provider', 'Proveedor'), ('provider-petition', 'Proveedor (Solicitud)'), ('provider-control', 'Proveedor (Grupos de control)'), ('provider-month', 'Proveedor (Meses)'), ('cluster', 'Cluster')], max_length=30, null=True)),
                ('action_text', models.CharField(blank=True, max_length=120, null=True)),
                ('action_verb', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('order', models.IntegerField(default=5)),
                ('icon', models.CharField(blank=True, max_length=30, null=True)),
                ('function_after', models.CharField(blank=True, max_length=100, null=True, verbose_name='Función llegando de Lambda')),
                ('finished_function', models.CharField(blank=True, max_length=100, null=True, verbose_name='Función al terminar hijos')),
                ('field_last_edit', models.CharField(blank=True, max_length=100, null=True, verbose_name='Campo de última edición')),
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
