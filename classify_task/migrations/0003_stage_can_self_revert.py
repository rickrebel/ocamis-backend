# Generated by Django 4.1.6 on 2024-09-05 19:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classify_task', '0002_run_python'),
    ]

    operations = [
        migrations.AddField(
            model_name='stage',
            name='can_self_revert',
            field=models.BooleanField(default=False),
        ),
    ]
