from django.core.management.base import BaseCommand

from intl_medicine.models import GroupAnswer


class Command(BaseCommand):
    help = 'Calcula si una respuesta de grupo es válida o no'

    def handle(self, *args, **options):
        group_answer = GroupAnswer.objects.filter(
            date_started__isnull=False,
            date_finished__isnull=False
        )
        print(f"Total de grupos a revisar: {group_answer.count()}")

        for ga in group_answer:
            ga.check_valid()
            print(f"Grupo {ga} es valido: {ga.is_valid}")
