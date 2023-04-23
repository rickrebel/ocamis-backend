# Generated by Django 4.1.6 on 2023-04-23 05:43

from django.db import migrations, models
import django.db.models.deletion
import inai.data_file_mixins.explore_mix
import inai.data_file_mixins.get_data_mix
import inai.data_file_mixins.utils_mix
import inai.models
import inai.petition_mixins.petition_mix
import inai.reply_file_mixins.process_mix


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('category', '0001_initial'),
        ('geo', '0001_initial'),
        ('data_param', '0001_initial'),
        ('classify_task', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(max_length=150, upload_to=inai.models.set_upload_path)),
                ('zip_path', models.TextField(blank=True, null=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('filtered_sheets', models.JSONField(blank=True, null=True, verbose_name='Nombres de las hojas filtradas')),
                ('suffix', models.CharField(blank=True, max_length=10, null=True)),
                ('directory', models.CharField(blank=True, max_length=255, null=True, verbose_name='Ruta en archivo comprimido')),
                ('error_process', models.JSONField(blank=True, null=True, verbose_name='Errores de procesamiento')),
                ('warnings', models.JSONField(blank=True, null=True, verbose_name='Advertencias')),
                ('total_rows', models.IntegerField(default=0)),
                ('sample_data', models.JSONField(blank=True, null=True, verbose_name='Primeros datos, de exploración')),
                ('sheet_names', models.JSONField(blank=True, null=True, verbose_name='Nombres de las hojas')),
                ('all_results', models.JSONField(blank=True, null=True, verbose_name='Todos los resultados')),
                ('completed_rows', models.IntegerField(default=0)),
                ('inserted_rows', models.IntegerField(default=0)),
                ('file_type', models.ForeignKey(blank=True, default='original_data', null=True, on_delete=django.db.models.deletion.CASCADE, to='category.filetype', verbose_name='Tipo de archivo')),
                ('origin_file', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='child_files', to='inai.datafile', verbose_name='archivo origen')),
            ],
            options={
                'verbose_name': 'Archivo con datos',
                'verbose_name_plural': '3. Archivos con datos',
                'ordering': ['-id'],
            },
            bases=(models.Model, inai.data_file_mixins.explore_mix.ExploreMix, inai.data_file_mixins.utils_mix.DataUtilsMix, inai.data_file_mixins.get_data_mix.ExtractorsMix),
        ),
        migrations.CreateModel(
            name='MonthAgency',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year_month', models.CharField(max_length=10)),
                ('agency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='months', to='geo.agency')),
            ],
            options={
                'verbose_name': 'Mes de entidad',
                'verbose_name_plural': 'Meses de entidad',
                'get_latest_by': 'year_month',
            },
        ),
        migrations.CreateModel(
            name='Petition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('folio_petition', models.CharField(max_length=50, verbose_name='Folio de la solicitud')),
                ('ask_extension', models.BooleanField(blank=True, null=True, verbose_name='Se solicitó extensión')),
                ('notes', models.TextField(blank=True, null=True)),
                ('send_petition', models.DateField(blank=True, null=True, verbose_name='Fecha de envío o recepción')),
                ('send_response', models.DateField(blank=True, null=True, verbose_name='Fecha de última respuesta')),
                ('description_petition', models.TextField(blank=True, null=True, verbose_name='descripción enviada')),
                ('description_response', models.TextField(blank=True, null=True, verbose_name='Respuesta texto')),
                ('description_complain', models.TextField(blank=True, null=True, verbose_name='Texto de la queja')),
                ('folio_complain', models.IntegerField(blank=True, null=True, verbose_name='Folio de la queja')),
                ('id_inai_open_data', models.IntegerField(blank=True, null=True, verbose_name='Id en el sistema de INAI')),
                ('info_queja_inai', models.JSONField(blank=True, help_text='Información de la queja en INAI Search', null=True, verbose_name='Datos de queja')),
                ('agency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='petitions', to='geo.agency')),
                ('invalid_reason', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='category.invalidreason', verbose_name='Razón de invalidez')),
                ('status_complain', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='petitions_complain', to='category.statuscontrol', verbose_name='Status de la queja')),
                ('status_data', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='petitions_data', to='category.statuscontrol', verbose_name='Status de los datos entregados')),
                ('status_petition', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='petitions_petition', to='category.statuscontrol', verbose_name='Status de la petición')),
            ],
            options={
                'verbose_name': 'Solicitud - Petición',
                'verbose_name_plural': '1. Solicitudes (Peticiones)',
            },
            bases=(models.Model, inai.petition_mixins.petition_mix.PetitionTransformsMix),
        ),
        migrations.CreateModel(
            name='SheetFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(max_length=255, upload_to=inai.models.set_upload_path)),
                ('matched', models.BooleanField(blank=True, null=True)),
                ('sheet_name', models.CharField(blank=True, max_length=255, null=True)),
                ('sample_data', models.JSONField(blank=True, default=inai.models.default_explore_data, null=True)),
                ('total_rows', models.IntegerField(default=0)),
                ('error_process', models.JSONField(blank=True, null=True)),
                ('warnings', models.JSONField(blank=True, null=True)),
                ('data_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sheet_files', to='inai.datafile')),
                ('file_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='category.filetype')),
                ('stage', models.ForeignKey(default='explore', on_delete=django.db.models.deletion.CASCADE, to='classify_task.stage', verbose_name='Etapa actual')),
                ('status', models.ForeignKey(default='finished', on_delete=django.db.models.deletion.CASCADE, to='classify_task.statustask')),
            ],
            options={
                'verbose_name': 'Archivo csv',
                'verbose_name_plural': '4. Archivos csv',
                'ordering': ['id'],
                'unique_together': {('data_file', 'sheet_name', 'file_type')},
            },
        ),
        migrations.CreateModel(
            name='ReplyFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(blank=True, max_length=150, null=True, upload_to=inai.models.set_upload_path, verbose_name='archivo')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('text', models.TextField(blank=True, null=True, verbose_name='Texto (en caso de no haber archivo)')),
                ('url_download', models.URLField(blank=True, max_length=400, null=True, verbose_name='Url donde se puede descargar el archivo')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Notas')),
                ('addl_params', models.JSONField(blank=True, null=True, verbose_name='Otras configuraciones')),
                ('has_data', models.BooleanField(default=False, verbose_name='Contiene los datos')),
                ('file_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='category.filetype')),
                ('petition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reply_files', to='inai.petition')),
            ],
            options={
                'verbose_name': 'Archivo sin datos finales',
                'verbose_name_plural': '2. Archivos sin datos finales',
            },
            bases=(models.Model, inai.reply_file_mixins.process_mix.ReplyFileMix),
        ),
        migrations.CreateModel(
            name='PetitionNegativeReason',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_main', models.BooleanField(verbose_name='Es la razón principal')),
                ('negative_reason', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='category.negativereason')),
                ('petition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='negative_reasons', to='inai.petition')),
            ],
            options={
                'verbose_name': 'Petición - razón negativa (m2m)',
                'verbose_name_plural': 'Peticiones - razones negativas (m2m)',
            },
        ),
        migrations.CreateModel(
            name='PetitionMonth',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notes', models.TextField(blank=True, null=True)),
                ('month_agency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inai.monthagency')),
                ('petition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='petition_months', to='inai.petition')),
            ],
            options={
                'verbose_name': 'Mes de solicitud',
                'verbose_name_plural': 'Meses de solicitud',
                'get_latest_by': 'month_agency__year_month',
            },
        ),
        migrations.CreateModel(
            name='PetitionFileControl',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_control', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='petition_file_control', to='data_param.filecontrol')),
                ('petition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='file_controls', to='inai.petition')),
            ],
            options={
                'verbose_name': 'Relacional: petición -- Grupo de Control',
                'verbose_name_plural': '7. Relacional: Petición -- Grupos de Control',
            },
        ),
        migrations.CreateModel(
            name='PetitionBreak',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(blank=True, null=True)),
                ('date_break', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='category.datebreak')),
                ('petition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='break_dates', to='inai.petition')),
            ],
            options={
                'verbose_name': 'Petición - fecha de corte (m2m)',
                'verbose_name_plural': 'Peticiones - fechas de corte (m2m)',
            },
        ),
        migrations.CreateModel(
            name='LapSheet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lap', models.IntegerField(default=0)),
                ('last_edit', models.DateTimeField(blank=True, null=True)),
                ('inserted', models.BooleanField(blank=True, default=False, null=True)),
                ('general_error', models.CharField(blank=True, max_length=255, null=True)),
                ('total_count', models.IntegerField(default=0)),
                ('processed_count', models.IntegerField(default=0)),
                ('prescription_count', models.IntegerField(default=0)),
                ('drug_count', models.IntegerField(default=0)),
                ('medical_unit_count', models.IntegerField(default=0)),
                ('area_count', models.IntegerField(default=0)),
                ('doctor_count', models.IntegerField(default=0)),
                ('diagnosis_count', models.IntegerField(default=0)),
                ('medicament_count', models.IntegerField(default=0)),
                ('discarded_count', models.IntegerField(default=0)),
                ('missing_rows', models.IntegerField(default=0)),
                ('missing_fields', models.IntegerField(default=0)),
                ('row_errors', models.JSONField(blank=True, null=True)),
                ('field_errors', models.JSONField(blank=True, null=True)),
                ('valid_insert', models.BooleanField(default=True)),
                ('sheet_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='laps', to='inai.sheetfile')),
            ],
            options={
                'verbose_name': 'Lap de archivo csv',
                'verbose_name_plural': '5. Laps de archivo csv',
                'ordering': ['id'],
                'unique_together': {('sheet_file', 'lap')},
            },
        ),
        migrations.AddField(
            model_name='datafile',
            name='petition_file_control',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='data_files', to='inai.petitionfilecontrol'),
        ),
        migrations.AddField(
            model_name='datafile',
            name='petition_month',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='inai.petitionmonth'),
        ),
        migrations.AddField(
            model_name='datafile',
            name='reply_file',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='data_file_childs', to='inai.replyfile', verbose_name='archivo base'),
        ),
        migrations.AddField(
            model_name='datafile',
            name='stage',
            field=models.ForeignKey(blank=True, default='initial', null=True, on_delete=django.db.models.deletion.CASCADE, to='classify_task.stage', verbose_name='Etapa actual'),
        ),
        migrations.AddField(
            model_name='datafile',
            name='status',
            field=models.ForeignKey(blank=True, default='finished', null=True, on_delete=django.db.models.deletion.CASCADE, to='classify_task.statustask', verbose_name='Status actual'),
        ),
        migrations.AddField(
            model_name='datafile',
            name='status_process',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='category.statuscontrol'),
        ),
        migrations.CreateModel(
            name='TableFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(max_length=255, upload_to=inai.models.set_upload_path)),
                ('is_for_edition', models.BooleanField(default=False)),
                ('collection', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='data_param.collection')),
                ('lap_sheet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='table_files', to='inai.lapsheet')),
            ],
            options={
                'verbose_name': 'Archivo para insertar',
                'verbose_name_plural': '6. Archivos para insertar',
                'ordering': ['id'],
                'unique_together': {('lap_sheet', 'collection', 'is_for_edition')},
            },
        ),
    ]
