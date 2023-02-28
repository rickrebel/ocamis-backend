
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
        .exclude(status_petition__name__icontains="mistake", )
    prefetch_petitions = Prefetch("petitions", queryset=filter_petitions)

    filter_petition_month = PetitionMonth.objects\
        .filter(month_entity__year_month__lte="202212")
    prefetch_petition_month = Prefetch(
        "petitions__petition_months",
        queryset=filter_petition_month)
    filter_month = MonthEntity.objects\
        .filter(year_month__lte="202212")
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


def build_quality_simple(file_ctrl):
    drug = None
    final_fields = file_ctrl["columns"]

    has_clues = ("CLUES", "clues") in final_fields or file_ctrl["has_ent_clues"]
    has_name = ("CLUES", "name") in final_fields
    if has_clues:
        clues = "enough"
    elif has_name:
        clues = "almost_enough"
    else:
        clues = "not_enough"
    emission = (("Prescription", "date_release") in final_fields or
                ("Prescription", "date_visit") in final_fields)
    entrega = ("Prescription", "fecha_entrega") in final_fields
    folio = ("Prescription", "folio_document") in final_fields
    if folio and emission and entrega:
        formula = "enough"
    elif folio and (emission or entrega):
        formula = "almost_enough"
    else:
        formula = "not_enough"
    official_key = ("Container", "key2") in final_fields
    prescrita = ("Drug", "prescribed_amount") in final_fields
    entregada = ("Drug", "delivered_amount") in final_fields
    no_entregada = ("Drug", "not_delivered_amount") in final_fields
    assortment = ("Drug", "clasif_assortment") in final_fields
    own_key = ("Container", "_own_key") in final_fields
    other_names = (
        ("Component", "name") in final_fields or
        ("Presentation", "description") in final_fields or
        ("Container", "name") in final_fields)
    if prescrita and (entregada or assortment or no_entregada):
        if official_key and (entregada or no_entregada):
            drug = "enough"
        elif official_key or other_names or own_key:
            drug = "almost_enough"
    if not drug:
        drug = "not_enough"
    return {"clues": clues, "formula": formula, "drug": drug}
