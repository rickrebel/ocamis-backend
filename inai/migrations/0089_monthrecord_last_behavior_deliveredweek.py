# Generated by Django 4.1.6 on 2024-06-10 17:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('med_cat', '0007_documenttype'),
        ('inai', '0088_remove_complaint_ask_extension_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='monthrecord',
            name='last_behavior',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='DeliveredWeek',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.IntegerField()),
                ('delivered', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='weeks', to='med_cat.delivered')),
                ('week_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deliveries', to='inai.weekrecord')),
            ],
            options={
                'verbose_name': 'Clasificación de entrega por semana',
                'verbose_name_plural': 'Clasificaciones de entrega por semana',
            },
        ),
    ]
