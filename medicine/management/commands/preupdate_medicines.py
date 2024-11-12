from django.core.management.base import BaseCommand

from medicine.models import Component, Presentation, Group


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.add_status_control()

        self.merge_components()

    def add_status_control(self):
        from category.models import StatusControl
        from medicine.views import medicine_status
        for status in medicine_status:
            StatusControl.objects.get_or_create(
                name=status["name"],
                defaults=dict(
                    group="medicament",
                    public_name=status["public_name"],
                    color=status["color"],
                    order=status["order"],
                    icon="medication",
                )
            )
        
        for group in Group.objects.all():
            group.save()

    def merge_components(self):

        components = [
            {
                "main": 540,
                "merge": 1220,
                "observation": "self.groups, PrioritizedComponent",
            },
            {
                "main": 780,
                "merge": 1254,
                "observation": "Presentation",
            },
            {
                "main": 1255,
                "merge": 1256,
                "observation": "Presentation, self.alias",
            },
            {
                "main": 833,
                "merge": 1240,
                "observation": "Presentation",
            },
        ]

        for component in components:
            main = Component.objects.get(pk=component["main"])
            merge = Component.objects.get(pk=component["merge"])

            main.groups.add(*merge.groups.all())
            merge.groups.clear()

            Presentation.objects.filter(component=merge).update(component=main)

            main_alias = [
                alias.upper().strip()
                for alias in (main.alias or "").split(",") if alias.strip()]
            merge_alias = [
                alias.upper().strip()
                for alias in (merge.alias or "").split(",") if alias.strip()]
            alias = list(set(main_alias + merge_alias))
            if alias:
                main.alias = ", ".join(alias)
                main.save()
            merge.delete()
