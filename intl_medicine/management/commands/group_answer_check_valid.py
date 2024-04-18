from django.core.management.base import BaseCommand

from intl_medicine.models import GroupAnswer


class Command(BaseCommand):
    help = 'Calcula si una respuesta de grupo es válida o no'

    def add_arguments(self, parser):
        parser.add_argument(
            '--seconds',
            dest='seconds',
            default=10,
            type=int,
            help='Tiempo en segundos para considerar una respuesta válida'
        )

    def handle(self, *args, **options):
        seconds = options['seconds']
        group_answer = GroupAnswer.objects.filter(
            date_started__isnull=False,
            date_finished__isnull=False
        )
        print(f"Total de grupos a revisar: {group_answer.count()}")

        for ga in group_answer:
            ga.check_valid(seconds=seconds)
            print(f"Grupo {ga} es valido: {ga.is_valid}")
