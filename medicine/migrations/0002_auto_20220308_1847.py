# Generated by Django 2.2.25 on 2022-03-09 00:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('medicine', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='component',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='medicine.Group'),
        ),
        migrations.AlterField(
            model_name='container',
            name='presentation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='containers', to='medicine.Presentation'),
        ),
        migrations.AlterField(
            model_name='presentation',
            name='component',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='presentations', to='medicine.Component'),
        ),
        migrations.AlterField(
            model_name='presentation',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='medicine.Group'),
        ),
        migrations.AlterField(
            model_name='presentation',
            name='presentation_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='medicine.PresentationType'),
        ),
        migrations.AlterField(
            model_name='presentationtype',
            name='agrupated_in',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='medicine.PresentationType'),
        ),
    ]
