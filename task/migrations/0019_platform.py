# Generated by Django 4.1.6 on 2023-04-16 05:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0018_remove_asynctask_table_file_asynctask_sheet_file'),
    ]

    operations = [
        migrations.CreateModel(
            name='Platform',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(max_length=10)),
                ('has_constrains', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Plataforma',
                'verbose_name_plural': 'Plataformas',
            },
        ),
    ]
