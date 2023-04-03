# Generated by Django 4.1.6 on 2023-03-29 17:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0035_area_aggregate_to_area_is_aggregate'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='area',
            name='delegation',
        ),
        migrations.AddField(
            model_name='area',
            name='institution',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='catalog.institution'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='area',
            name='state',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalog.state'),
        ),
    ]
