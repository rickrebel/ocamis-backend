# Generated by Django 4.1.6 on 2023-03-30 04:46

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('formula', '0017_rename_clave_doctor_doctor_clave_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='diagnosis',
            name='id',
        ),
        migrations.AddField(
            model_name='diagnosis',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]
