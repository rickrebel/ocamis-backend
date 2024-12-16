

def identify_duplicated_petitions():
    from inai.models import Petition
    from django.db.models import Count
    duplicated_petitions = Petition.objects.values('folio_petition')\
        .annotate(folio_count=Count('folio_petition'))\
        .filter(folio_count__gt=1)
    for petition in duplicated_petitions:
        print(petition)
    # print(duplicated_petitions)



