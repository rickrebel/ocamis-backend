# Generated by Django 2.2.25 on 2022-07-22 19:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('files_rows', '0005_auto_20220722_1451'),
        ('recipe', '0007_auto_20220722_1217'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recipe',
            name='file',
        ),
        migrations.AddField(
            model_name='medicine',
            name='file',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='files_rows.File'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='recipe',
            name='type_document',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='recipe.DocumentType'),
        ),
    ]
