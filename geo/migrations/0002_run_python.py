from django.db import migrations


def copy_old_values(apps, schema_editor):
    OldStatusControl = apps.get_model("category", "OldStatusControl")
    Provider = apps.get_model("geo", "Provider")
    for old_status in OldStatusControl.objects.all():
        Provider.objects.filter(old_status_opera=old_status)\
                .update(status_operative=old_status.name)


def reclassify_status(apps, schema_editor):
    Provider = apps.get_model('geo', 'Provider')
    for provider in Provider.objects.all():
        if provider.status_priority_id == 'no_data':
            provider.status_priority_id = 'no_info'
        else:
            provider.status_priority_id = 'medium_priority'
        provider.save()


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(copy_old_values),
        migrations.RunPython(reclassify_status),
    ]
