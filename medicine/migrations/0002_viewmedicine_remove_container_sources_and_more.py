# Generated by Django 4.1.6 on 2024-11-05 03:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0002_alter_datebreak_group_alter_filetype_group_and_more'),
        ('medicine', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ViewMedicine',
            fields=[
                ('container_id', models.IntegerField(primary_key=True, serialize=False)),
                ('key', models.CharField(max_length=20)),
                ('key2', models.CharField(max_length=20)),
                ('container_name', models.TextField()),
                ('presentation_id', models.IntegerField()),
                ('presentation_name', models.TextField()),
                ('component_id', models.IntegerField()),
                ('component_name', models.TextField()),
                ('priority', models.IntegerField()),
            ],
            options={
                'verbose_name': 'Medicamento',
                'verbose_name_plural': '5. Medicamentos',
                'db_table': 'view_medicine',
                'managed': False,
            },
        ),
        migrations.RemoveField(
            model_name='container',
            name='sources',
        ),
        migrations.AddField(
            model_name='component',
            name='source_data',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
        migrations.AddField(
            model_name='component',
            name='status_final',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='components_final', to='category.statuscontrol'),
        ),
        migrations.AddField(
            model_name='component',
            name='status_review',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='components_review', to='category.statuscontrol'),
        ),
        migrations.AddField(
            model_name='container',
            name='source_data',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
        migrations.AddField(
            model_name='container',
            name='status_review',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='category.statuscontrol'),
        ),
        migrations.AddField(
            model_name='presentation',
            name='source_data',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
        migrations.AddField(
            model_name='presentation',
            name='status_final',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='presentations_final', to='category.statuscontrol'),
        ),
        migrations.AddField(
            model_name='presentation',
            name='status_review',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='presentations_review', to='category.statuscontrol'),
        ),
    ]
