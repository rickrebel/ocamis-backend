# Generated by Django 4.1.6 on 2024-03-24 02:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inai', '0066_variable_requesttemplate'),
    ]

    operations = [
        migrations.AddField(
            model_name='variable',
            name='request_template',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='variables', to='inai.requesttemplate'),
            preserve_default=False,
        ),
    ]
