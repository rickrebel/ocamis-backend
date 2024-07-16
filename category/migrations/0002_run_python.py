from django.db import migrations


def copy_old_status_control(apps, schema_editor):
    OldStatusControl = apps.get_model("category", "OldStatusControl")
    StatusControl = apps.get_model("category", "StatusControl")
    for old_status in OldStatusControl.objects.all():
        StatusControl.objects.create(
            name=old_status.name,
            group=old_status.group,
            public_name=old_status.public_name,
            color=old_status.color,
            icon=old_status.icon,
            order=old_status.order,
            description=old_status.description,
            addl_params=old_status.addl_params,
        )


def recover_official_name(apps, schema_editor):
    StatusControl = apps.get_model('category', 'StatusControl')
    official_names = ["En proceso",
                      "En proceso, información adicional",
                      "En proceso con prórroga",
                      "Terminada",
                      "Vencida"]
    for status in StatusControl.objects.filter(group='petition'):
        if status.public_name in official_names:
            status.official_name = status.public_name
            status.save()


def set_is_official(apps, schema_editor):
    InvalidReason = apps.get_model("category", "InvalidReason")
    for reason in InvalidReason.objects.all():
        if reason.name.startswith("Desechada"):
            reason.set_is_official = True
            reason.save()


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(copy_old_status_control),
        migrations.RunPython(recover_official_name),
        migrations.RunPython(set_is_official),
    ]
