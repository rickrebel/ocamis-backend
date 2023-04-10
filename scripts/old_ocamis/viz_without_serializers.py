
@action(methods=["get"], detail=False, url_path='data_viz')
def data_viz(self, request, **kwargs):
    from geo.api.final_viz import fetch_agencies
    #import json

    operability = {
        "ideal": {
            "formats": ["csv", "json", "txt"],
            "anomalies": [],
            "others": [],
        },
        "aceptable": {
            "formats": ["xls"],
            "anomalies": [
                "code_headers",
                "no_headers",
                "hide_colums_tabs"
            ],
            "others": [],
        },
        "enhaced": {
            "formats": [],
            "anomalies": [
                "different_tipe_tabs",
                "internal_catalogue",
                "hide_colums_tabs",
                "no_valid_row_data",
                "concatenated"
                "same_group_data",
                #solo para local:
                "abasdf",
            ],
            "others": ["many_file_controls"],
        },
        "impeachable": {
            "formats": ["pdf", "word", "email", "other"],
            "anomalies": ["row_spaces"],
            "others": [],
        },
    }
    enoughs = ["not_enough", "enough", "almost_enough", "not_enough"]

    pilot = request.query_params.get("is_pilot", "false")
    is_pilot = pilot.lower() in ["si", "yes", "true"]
    include_groups = ["detailed", "stock"]
    all_agencies = fetch_agencies(include_groups)
    if is_pilot:
        all_agencies = all_agencies.filter(is_pilot=True)

    #serializer = self.get_serializer_class()(
    #    all_agencies, many=True, context={'request': request})

    final_data = []
    status_no_data = ["no_data", "waiting", "pick_up"]
    #for agency in serializer.data:
    for agency in all_agencies:
        for petition in agency.petitions.all():
            status_data = petition.status_data
            for data_group in include_groups:
                file_ctrls = [
                    file_ctrl for file_ctrl in petition.file_controls.all()
                    if file_ctrl.data_group.name == data_group ]
                file_formats = [
                    file_ctrl.format_file for file_ctrl in file_ctrls]
                anomalies = []
                for file_ctrl in file_ctrls:
                    anomalies += file_ctrl.anomalies.all()\
                        .values_list("name", flat=True)
                file_ctrls_count = len(file_ctrls)
                many_file_controls = file_ctrls_count > 1
                final_operativ = None
                for (curr_operativ, params) in operability.items():
                    if not set(params["formats"]).isdisjoint(set(file_formats)):
                        final_operativ = curr_operativ
                    if not set(params["anomalies"]).isdisjoint(set(anomalies)):
                        final_operativ = curr_operativ
                    for other in params["others"]:
                        if locals()[other]:
                            final_operativ = curr_operativ
                if not status_data or status_data.name in status_no_data:
                    final_operativ = "no_data"
                setattr(petition, "data_group", {
                    "file_formats": file_formats,
                    "many_file_controls": many_file_controls,
                    "operativ": final_operativ,
                    "file_ctrls_count": file_ctrls_count,
                })

                if data_group != "detailed":
                    continue
                clues = 0
                formula = 0
                drug = 0
                for file_ctrl in file_ctrls:
                    final_fields = file_ctrl.columns\
                        .filter(final_field__need_for_viz=True)\
                        .values_list(
                            "final_field__collection__model_name",
                            "final_field__name")
                    final_fields = tuple(final_fields)
                    has_clues = (("CLUES", "clues") in final_fields or
                        agency.clues)
                    has_name = ("CLUES", "name") in final_fields
                    if has_clues and clues < 2:
                        clues = 1
                    elif (has_clues or has_name) and clues < 3:
                        clues = 2
                    else:
                        clues = 3
                    emision = (("Prescription", "date_release") in final_fields or
                        ("Prescription", "fecha_consulta") in final_fields)
                    entrega = ("Prescription", "fecha_entrega") in final_fields
                    folio = ("Prescription", "folio_document") in final_fields
                    if folio and emision and entrega and formula < 2:
                        formula = 1
                    elif folio and (emision or entrega) and formula < 3:
                        formula = 2
                    else:
                        formula = 3
                    official_key = ("Container", "key2") in final_fields
                    prescrita = ("Drug", "prescribed_amount") in final_fields
                    entregada = ("Drug", "delivered_amount") in final_fields
                    own_key = ("Container", "own_key2") in final_fields
                    other_names = (("Drug", "drug_name") in final_fields or
                        ("Presentation", "description") in final_fields or
                        ("Container", "name") in final_fields)
                    if prescrita and entregada:
                        if official_key and drug < 2:
                            drug = 1
                        elif (official_key or other_names or own_key) and drug < 3:
                            drug = 2
                    if not drug:
                        drug = 3
                pet_dg = setattr(petition, data_group, {})
                if not status_data or status_data.name in status_no_data:
                    pet_dg.clues = "no_data"
                    pet_dg.formula = "no_data"
                    pet_dg.drug = "no_data"
                    pet_dg.qual_detailed = "no_data"
                else:
                    pet_dg.clues = enoughs[clues]
                    pet_dg.formula = enoughs[formula]
                    pet_dg.drug = enoughs[drug]
                    max_value = max([clues, formula, drug])
                    pet_dg.qual_detailed = enoughs[max_value]

        final_data.append(agency)

    #return Response(
    #    serializer.data, status=status.HTTP_200_OK)
    return Response(final_data, status=status.HTTP_200_OK)

