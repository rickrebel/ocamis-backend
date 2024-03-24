# Generated by Django 4.1.6 on 2024-03-23 17:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0016_alter_asynctask_user_alter_clickhistory_user_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='offlinetask',
            name='activity_type',
            field=models.CharField(choices=[('weekly_meeting', 'Reunión semanal'), ('meeting', 'Reunión'), ('training', 'Capacitación'), ('pnt', 'Solicitudes INAI'), ('other', 'Otro')], max_length=100, verbose_name='Tipo'),
        ),
    ]
