
def fetch_entities(include_groups):
    from django.db.models import Prefetch
    from catalog.models import Entity
    from inai.models import (
        NameColumn, Petition, FileControl, PetitionMonth, MonthEntity)

    filter_columns = NameColumn.objects.filter(
        final_field__isnull=False, final_field__need_for_viz=True)
    prefetch_columns = Prefetch(
        "petitions__file_controls__file_control__columns", 
        queryset=filter_columns)
    filter_petitions = Petition.objects\
        .exclude(status_petition__name="mistake", )
    prefetch_petitions = Prefetch("petitions", queryset=filter_petitions)
    
    filter_petition_month = PetitionMonth.objects\
        .filter(month_entity__year_month__lt="202207")
    prefetch_petition_month = Prefetch(
        "petitions__petition_months",
        queryset=filter_petition_month)
    filter_month = MonthEntity.objects\
        .filter(year_month__lt="202207")
    prefetch_month = Prefetch("months", queryset=filter_month)
    filter_file_control = FileControl.objects\
        .filter(data_group__name__in=include_groups)
    prefetch_file_control = Prefetch(
        "petitions__file_controls__file_control",
        queryset=filter_file_control)
    all_entities = Entity.objects\
        .filter(competent=True, vigencia=True)\
        .prefetch_related(
            "institution",
            "clues",
            "state",
            #"months"
            prefetch_month,
            #"petitions",
            prefetch_petitions,
            "petitions__status_data",
            "petitions__status_petition",
            prefetch_petition_month,
            #"petitions__petition_months",
            "petitions__negative_reasons",
            "petitions__petition_months__month_entity",
            #prefetch_file_control,
            "petitions__file_controls__file_control",
            "petitions__file_controls__file_control__data_group",
            prefetch_columns,
            "petitions__file_controls__file_control__columns__final_field",
            "petitions__file_controls__file_control"\
                "__columns__final_field__collection",
        )
    return all_entities
