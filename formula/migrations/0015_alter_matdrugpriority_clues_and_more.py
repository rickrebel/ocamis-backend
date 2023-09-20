# Generated by Django 4.1.6 on 2023-09-20 17:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0011_alter_entity_options'),
        ('medicine', '0005_component_description'),
        ('formula', '0014_alter_matdrugtotals_clues_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matdrugpriority',
            name='clues',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='geo.clues'),
        ),
        migrations.AlterField(
            model_name='matdrugpriority',
            name='container',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='medicine.container'),
        ),
        migrations.AlterField(
            model_name='matdrugpriority',
            name='delegation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='geo.delegation'),
        ),
        migrations.AlterField(
            model_name='matdrugpriority',
            name='key',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
