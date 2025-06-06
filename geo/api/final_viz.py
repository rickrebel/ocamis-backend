
def fetch_agencies(include_groups):
    from django.db.models import Prefetch
    from geo.models import Agency
    from inai.models import Petition
    from data_param.models import NameColumn
    from data_param.models import FileControl

    filter_columns = NameColumn.objects.filter(
        final_field__isnull=False, final_field__need_for_viz=True)
    prefetch_columns = Prefetch(
        "petitions__file_controls__file_control__columns",
        queryset=filter_columns)
    filter_petitions = Petition.objects.exclude(status_petition_id="mistake")
    prefetch_petitions = Prefetch("petitions", queryset=filter_petitions)

    # RICK Otros Este filtro por mes ya no lo estamos haciendo
    # filter_petition_month = PetitionMonth.objects\
    #     .filter(month_agency__year_month__lte="2023-02")
    # prefetch_petition_month = Prefetch(
    #     "petitions__petition_months",
    #     queryset=filter_petition_month)
    # filter_month = MonthRecord.objects\
    #     .filter(year_month__lte="2023-02")
    # prefetch_month = Prefetch("months", queryset=filter_month)
    filter_file_control = FileControl.objects\
        .filter(data_group_id__in=include_groups)
    prefetch_file_control = Prefetch(
        "petitions__file_controls__file_control",
        queryset=filter_file_control)
    all_agencies = Agency.objects\
        .filter(competent=True, vigencia=True)\
        .prefetch_related(
            "institution",
            "clues",
            "state",
            # "months"
            # prefetch_month,
            # "petitions",
            prefetch_petitions,
            # prefetch_petition_month,
            "petitions__month_records",
            # RICK Otros checar si es to es necesario
            # "petitions__month_records__month_record",
            "petitions__negative_reasons",
            # prefetch_file_control,
            "petitions__file_controls__file_control",
            "petitions__file_controls__file_control",
            prefetch_columns,
            "petitions__file_controls__file_control__columns__final_field",
            "petitions__file_controls__file_control"
            "__columns__final_field__collection",
        )
    return all_agencies


def build_quality_simple(file_ctrl):
    drug = None
    final_fields = file_ctrl["columns"]

    def has_field(field, is_unique=None):
        [model, field] = field.split(":")
        if is_unique is None:
            return (model, field, True) in final_fields \
                or (model, field, False) in final_fields
        else:
            return (model, field, is_unique) in final_fields

    def has_unique_field(model, is_unique=True):
        for field in final_fields:
            if field[0] == model and field[2] == is_unique:
                return True
        return False

    has_clues_unique = has_unique_field("MedicalUnit")
    has_clues_other = has_unique_field("MedicalUnit", False)
    if has_clues_unique:
        clues = "enough"
    elif has_clues_other:
        clues = "almost_enough"
    else:
        clues = "not_enough"
    emission = (has_field("Rx:date_release") or
                has_field("Rx:date_visit"))
    entrega = has_field("Rx:date_delivery")
    folio = has_field("Rx:folio_document")
    if folio and emission and entrega:
        formula = "enough"
    elif folio and (emission or entrega):
        formula = "almost_enough"
    else:
        formula = "not_enough"
    official_key = has_field("Medicament:key2")
    prescrita = has_field("Drug:prescribed_amount")
    entregada = has_field("Drug:delivered_amount")
    returned = has_field("Drug:return_amount")
    no_entregada = has_field("Drug:not_delivered_amount")
    assortment = has_field("Drug:clasif_assortment")
    assortment_prescribed = has_field("Delivered:clasif_assortment_presc")
    some_assortment = assortment or assortment_prescribed

    own_key = has_field("Medicament:own_key2")
    other_names = (
        has_field("Medicament:component_name") or
        has_field("Medicament:presentation_description") or
        has_field("Medicament:container_name"))
    if prescrita and (entregada or some_assortment or no_entregada):
        if official_key and (entregada or no_entregada or returned):
            drug = "enough"
        elif official_key or other_names or own_key:
            drug = "almost_enough"
    if not drug:
        drug = "not_enough"
    return {"clues": clues, "formula": formula, "drug": drug}
