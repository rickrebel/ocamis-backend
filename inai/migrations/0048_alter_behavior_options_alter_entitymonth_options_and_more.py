# Generated by Django 4.1.6 on 2023-07-10 20:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('classify_task', '0004_taskfunction_is_queueable_and_more'),
        ('inai', '0047_alter_crossingsheet_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='behavior',
            options={'verbose_name': 'Comportamiento Merge', 'verbose_name_plural': 'CAT. Comportamientos Merge'},
        ),
        migrations.AlterModelOptions(
            name='entitymonth',
            options={'get_latest_by': 'year_month', 'ordering': ['year_month'], 'verbose_name': '8. Mes-proveedor', 'verbose_name_plural': '8. Meses-proveedores'},
        ),
        migrations.AlterModelOptions(
            name='entityweek',
            options={'get_latest_by': ['year_month', 'year_week'], 'verbose_name': 'Semana-proveedor', 'verbose_name_plural': '9. Semanas-proveedores'},
        ),
        migrations.AddField(
            model_name='entitymonth',
            name='stage',
            field=models.ForeignKey(default='explore', on_delete=django.db.models.deletion.CASCADE, to='classify_task.stage', verbose_name='Etapa actual'),
        ),
        migrations.AddField(
            model_name='entitymonth',
            name='status',
            field=models.ForeignKey(default='finished', on_delete=django.db.models.deletion.CASCADE, to='classify_task.statustask'),
        ),
        migrations.AddField(
            model_name='entityweek',
            name='crosses',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
