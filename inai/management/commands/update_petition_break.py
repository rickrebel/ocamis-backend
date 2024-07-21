import os
from django.core.management.base import BaseCommand, CommandParser
from django.conf import settings

from inai.models import PetitionBreak


def update_petition_date(date_attr_name, overwrite, ignore_blank):
    query_pb = PetitionBreak.objects.filter(date_break__name=date_attr_name)
    print(f"PetitionBreaks {date_attr_name} encontrados: {query_pb.count()}")
    for petition_brake in PetitionBreak.objects.filter(date_break__name=date_attr_name):
        petition = petition_brake.petition
        
        if petition_brake.date is None and ignore_blank:
            continue

        if getattr(petition, date_attr_name) and not overwrite:
            continue

        setattr(petition, date_attr_name, petition_brake.date)
        petition.save()

    print(f"Petition.{date_attr_name} actualizado")


class Command(BaseCommand):
    help = 'Actualiza response_limit y complain_send_limit de Petition en base a PetitionBreak'

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            '--overwrite', type=int, help='Indica si se sobreescribiran los '
            'valores de PetitionBreak sobre Petition, si ya existen')
        parser.add_argument(
            '--ignore_blank', type=int, help='Si PetitionBreak.date es None,'
            ' no se actualiza el valor de Petition')

    def handle(self, *args, **kwargs):
        overwrite = kwargs.get('overwrite', 0)
        ignore_blank = kwargs.get('ignore_blank', 0)
        update_petition_date("response_limit", overwrite, ignore_blank)
        update_petition_date("complain_send_limit", overwrite, ignore_blank)
