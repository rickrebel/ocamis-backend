# Generated by Django 4.1.6 on 2024-07-02 18:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('formula', '0024_delete_documenttype_remove_drug_date_closed_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rx',
            name='folio_ocamis',
            field=models.CharField(max_length=70),
        ),
    ]
