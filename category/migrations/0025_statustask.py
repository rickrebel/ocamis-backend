# Generated by Django 4.1.6 on 2023-02-11 23:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0024_alter_datebreak_break_params_and_more'),
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
            ],
            options={
                'verbose_name': 'Estado de tarea',
                'verbose_name_plural': 'Estados de tareas',
                'ordering': ['order'],
            },
        ),
    ]
