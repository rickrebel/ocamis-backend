# Generated by Django 4.1.6 on 2023-05-05 19:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0001_initial'),
        ('inai', '0002_lapsheet_real_missing_rows'),
    ]

    operations = [
        migrations.AlterField(
            model_name='replyfile',
            name='file_type',
            field=models.ForeignKey(blank=True, default='no_final_info', null=True, on_delete=django.db.models.deletion.CASCADE, to='category.filetype'),
        ),
    ]
