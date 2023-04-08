

from category.models import NegativeReason
from inai.models import PetitionNegativeReason
from data_param.models import FileControl
from geo.models import Agency, CLUES
from django.db.models import Count

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
    .values('petition__agency__name', 'petition__agency__acronym')\
    .annotate(total=Count("petition__agency__name"))\
    .values('total', 'petition__agency__name', 'petition__eagency__acronym')\
    .order_by("-total")

for agency in ordered_freq_by_id:
    print(agency)


agencies = Agency.objects\
    .filter(petitions__negative_reasons__negative_reason_id=2)\
    .values('acronym', 'name')\
    .distinct()\

# ordered_negatives[:5]


totalclu = CLUES.objects.all()\
    .values('institution')\
    .annotate(total_clues = Count('institution'))\
    .order_by('-total_clues')


# PetitionNegativeReason.objects.all(petititon__ negative_reason__name=)


agencies = FileControl.objects\
    .filter(anomalies__in=[3, 4])\
    .values('petition_file_control__petition__agency__name')\
    .annotate(total=Count("petition_file_control__petition__agency__name"))\
    .values('total', 'petition_file_control__petition__agency__name')\
    .order_by("-total")


for agency in agencies:
    print(agency)





