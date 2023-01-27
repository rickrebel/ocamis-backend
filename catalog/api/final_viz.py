
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
        .filter(month_entity__year_month__lt="202212")
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
    clues = None
    formula = None
    droug = None
    final_fields = file_ctrl["columns"]
    
    has_clues = ("CLUES", "clues") in final_fields or file_ctrl["has_ent_clues"]
    has_name = ("CLUES", "name") in final_fields
    if has_clues:
        clues = "enough"
    elif has_name:
        clues = "almost_enough"
    else:
        clues = "not_enough"
    emision = (("Prescription", "fecha_emision") in final_fields or
        ("Prescription", "fecha_consulta") in final_fields)
    entrega = ("Prescription", "fecha_entrega") in final_fields
    folio = ("Prescription", "folio_documento") in final_fields
    if folio and emision and entrega:
        formula = "enough"
    elif folio and (emision or entrega):
        formula = "almost_enough"
    else:
        formula = "not_enough"
    official_key = ("Container", "key2") in final_fields
    prescrita = ("Droug", "cantidad_prescrita") in final_fields
    entregada = ("Droug", "cantidad_entregada") in final_fields
    assortment = ("Droug", "clasif_assortment") in final_fields
    own_key = ("Container", "_own_key") in final_fields
    other_names = (("Droug", "droug_name") in final_fields or
        ("Presentation", "description") in final_fields or
        ("Container", "name") in final_fields)
    if prescrita and (entregada or assortment):
        if official_key and entregada:
            droug = "enough"
        elif official_key or other_names or own_key:
            droug = "almost_enough"
    if not droug:
        droug = "not_enough"
    return {"clues": clues, "formula": formula, "droug": droug}



def build_quality(entity, file_ctrls):
    clues = 0
    formula = 0
    droug = 0
    for file_ctrl in file_ctrls:
        final_fields = file_ctrl["columns"]
        has_clues = (("CLUES", "clues") in final_fields or 
            entity["clues"])
        has_name = ("CLUES", "name") in final_fields
        if has_clues and clues < 2:
            clues = 1
        elif (has_clues or has_name) and clues < 3:
            clues = 2
        else:
            clues = 3
        emision = (("Prescription", "fecha_emision") in final_fields or
            ("Prescription", "fecha_consulta") in final_fields)
        entrega = ("Prescription", "fecha_entrega") in final_fields
        folio = ("Prescription", "folio_documento") in final_fields
        if folio and emision and entrega and formula < 2:
            formula = 1
        elif folio and (emision or entrega) and formula < 3:
            formula = 2
        else:
            formula = 3
        official_key = ("Container", "key2") in final_fields
        prescrita = ("Droug", "cantidad_prescrita") in final_fields
        entregada = ("Droug", "cantidad_entregada") in final_fields
        own_key = ("Container", "_own_key") in final_fields
        other_names = (("Droug", "droug_name") in final_fields or
            ("Presentation", "description") in final_fields or
            ("Container", "name") in final_fields)
        if prescrita and entregada:
            if official_key and droug < 2:
                droug = 1
            elif (official_key or other_names or own_key) and droug < 3:
                droug = 2
        if not droug:
            droug = 3
    return clues, formula, droug
