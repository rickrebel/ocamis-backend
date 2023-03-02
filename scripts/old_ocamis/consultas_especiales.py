

from category.models import NegativeReason
from inai.models import PetitionNegativeReason
from data_param.models import FileControl
from catalog.models import Entity
from django.db.models import Q, Count

NegativeReason.objects.all()\
    .values('petitionnegativereason')\
    .annotate(total=Count("name"))\
    .values('total', 'name')

ordered_negatives = PetitionNegativeReason.objects.all()\
    .values('negative_reason__name')\
    .annotate(total=Count("negative_reason__name"))\
    .values('total', 'negative_reason__name', 'negative_reason__id')\
    .order_by("-total")


ordered_freq_by_id = PetitionNegativeReason.objects\
    .filter(negative_reason__id=2)\
    .values('petition__entity__name', 'petition__entity__acronym')\
    .annotate(total=Count("petition__entity__name"))\
    .values('total', 'petition__entity__name', 'petition__entity__acronym')\
    .order_by("-total")

for entity in ordered_freq_by_id:
    print(entity)


entities = Entity.objects\
    .filter(petitions__negative_reasons__negative_reason_id=2)\
    .values('acronym', 'name')
    .distinct()\

ordered_negatives[:5]


totalclu = CLUES.objects.all()\
    .values('institution')\
    .annotate(total_clues = Count('institution'))\
    .order_by('-total_clues')


PetitionNegativeReason.objects.all(petititon__ negative_reason__name=)


entities = FileControl.objects\
    .filter(anomalies__in=[3, 4])\
    .values('petition_file_control__petition__entity__name')\
    .annotate(total=Count("petition_file_control__petition__entity__name"))\
    .values('total', 'petition_file_control__petition__entity__name')\
    .order_by("-total")


for entity in entities:
    print(entity)





