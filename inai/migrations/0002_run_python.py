# Generated by Django 4.1.13 on 2024-07-16 08:14

from django.db import migrations


def copy_old_values(apps, schema_editor):
    OldStatusControl = apps.get_model("category", "OldStatusControl")
    Petition = apps.get_model("inai", "Petition")
    for old_status in OldStatusControl.objects.all():
        Petition.objects.filter(old_status_complain=old_status)\
                .update(status_complain=old_status.name)
        Petition.objects.filter(old_status_data=old_status)\
                .update(status_data=old_status.name)
        Petition.objects.filter(old_status_petition=old_status)\
                .update(status_petition=old_status.name)


def recover_complain_data(apps, schema_editor):
    Petition = apps.get_model("inai", "Petition")
    Complaint = apps.get_model("inai", "Complaint")
    for petition in Petition.objects.filter(info_queja_inai__isnull=False):
        json_data = petition.info_queja_inai
        folio_complaint = json_data.get("EXPEDIENTE")
        complaint = Complaint.objects.create(
            petition=petition,
            folio_complaint=folio_complaint,
            info_queja_inai=json_data,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('inai', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(copy_old_values),
        # migrations.RunPython(recover_complain_data),
    ]
