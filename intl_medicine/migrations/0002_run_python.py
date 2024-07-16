# Generated by Django 4.1.13 on 2024-07-16 08:15

from django.db import migrations


def delete_prioritized_component(apps, schema_editor):
    PrioritizedComponent = apps.get_model(
        "intl_medicine", "PrioritizedComponent")
    PrioritizedComponent.objects.all().delete()


def create_group_answer(apps, schema_editor):
    GroupAnswer = apps.get_model("intl_medicine", "GroupAnswer")
    Group = apps.get_model("medicine", "Group")
    for group in Group.objects.all():
        new_group_answer = GroupAnswer()
        new_group_answer.group = group
        new_group_answer.save()


class Migration(migrations.Migration):

    dependencies = [
        ('intl_medicine', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_group_answer),
    ]
