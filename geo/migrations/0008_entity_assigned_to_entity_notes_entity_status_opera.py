# Generated by Django 4.1.6 on 2023-07-17 19:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('category', '0001_initial'),
        ('geo', '0007_entity_is_pilot'),
    ]

    operations = [
        migrations.AddField(
            model_name='entity',
            name='assigned_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Asignado a'),
        ),
        migrations.AddField(
            model_name='entity',
            name='notes',
            field=models.TextField(blank=True, null=True, verbose_name='Notas'),
        ),
        migrations.AddField(
            model_name='entity',
            name='status_opera',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='category.statuscontrol', verbose_name='Status de los registro de variables'),
        ),
    ]
