# Generated by Django 4.1.6 on 2024-01-10 18:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('intl_medicine', '0004_groupanswer_comments'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='prioritizedcomponent',
            name='date',
        ),
    ]
