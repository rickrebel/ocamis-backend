
def unescape(val, petition):
    import html
    return html.unescape(val)


def add_br(val, petition):
    return val.replace("\n", "<br>")


def date_mex(val, petition=None):
    from datetime import datetime
    try:
        return datetime.strptime(val, "%d/%m/%Y")
    except Exception as e:
        print("Error en la fecha: ", val)
        print(e)
        return None


def to_json_old(val, petition):
    import json
    return json.loads(val)


def to_json(value, petition):
    from inai.models import Complaint
    import json
    try:
        val = json.loads(value)
    except Exception as e:
        print("Error en la conversión a JSON")
        print(e)
        return
    folio_complaint = val.get("EXPEDIENTE", False)
    if not folio_complaint:
        return
    try:
        complaint = petition.complaints.get(folio_complaint=folio_complaint)
    except Complaint.DoesNotExist:
        complaint = Complaint.objects.create(
            folio_complaint=folio_complaint, petition=petition)
    complaint.save_json_data(val)


def get_status_obj(val, petition):
    from category.models import InvalidReason, StatusControl
    status_found = None
    try:
        status_found = StatusControl.objects.get(
            official_name=val, group="petition")
    except StatusControl.DoesNotExist:
        pass
    if not status_found:
        try:
            status_found = StatusControl.objects.get(
                addl_params__icontains=val, group="petition")
        except StatusControl.DoesNotExist:
            print("No encontramos el status: ", val)
    if val == "Desechada por falta de respuesta del ciudadano":
        invalid_reason = InvalidReason.objects.get(name="Desechada")
        petition.invalid_reason = invalid_reason
        petition.save()
    elif val == "Desechada por falta de selección del medio de entrega":
        try:
            invalid_reason = InvalidReason.objects.get(name="Desechada 2")
        except InvalidReason.DoesNotExist:
            invalid_reason = InvalidReason.objects.create(
                name="Desechada 2",
                is_official=True,
                description="Desechada por falta de selección del medio de entrega",
            )
        petition.invalid_reason = invalid_reason
        petition.save()
    if not status_found:
        return petition.status_petition
    elif not petition.status_petition:
        return status_found
    elif petition.status_petition.order > status_found.order:
        return petition.status_petition
    else:
        return status_found


def join_url(value, petition):
    from respond.models import ReplyFile
    # if ReplyFile.objects.filter(petition=petition, url_download__isnull=False)
    # .exists():
    #     return
    if "https" not in value:
        default_url = "https://descarga.plataformadetransparencia.org.mx/buscador-ws/descargaArchivo/SISAI/"
        value = "%s%s" % (default_url, value)
    try:
        ReplyFile.objects.get_or_create(petition=petition, url_download=value)
    except Exception as e:
        print("No se pudo crear el archivo")
        print(e)


def add_limit_complain(row, main):
    from inai.models import PetitionBreak
    from category.models import DateBreak

    try:
        default_break = DateBreak.objects.get(name="response_limit")
    except Exception as e:
        print("No se encontró el tipo de DateBreak response_limit")
        print(e)
        return
    final_date = date_mex(row["Fecha límite de entrega"], None)
    try:
        petition_break, created_pb = PetitionBreak.objects.get_or_create(
            petition=main, date_break=default_break)
        petition_break.date = final_date
        petition_break.save()
    except Exception as e:
        print("No se pudo crear la fecha", main)
        print(e)
        pass


def join_lines(row, main):
    from inai.models import Petition
    curr_value = row.get("datosAdicionales", False)
    if curr_value:
        curr_value = main.description_petition + "\n\n--------------\n\n" + curr_value
        main_obj = Petition.objects.filter(id=main.id)
        if main_obj[0].description_petition != curr_value:
            main_obj.update(description_petition=curr_value)


def insert_between_months(row, petition):
    from inai.models import MonthRecord
    from datetime import datetime
    # print(petition.send_petition)
    if petition.send_petition:
        month = petition.send_petition.month
        year = petition.send_petition.year
    else:
        month = datetime.now().month
        year = datetime.now().year
    if month == 1:
        month = 12
        year = year - 1
    else:
        month = month - 1

    curr_year_month = f"{year}-{month:02d}"
    provider = petition.real_provider or petition.agency.provider
    month_records = MonthRecord.objects.filter(provider=provider)
    month_record = month_records.filter(year_month=curr_year_month).first()
    if not month_record:
        month_record = MonthRecord.objects.create(
            provider=provider, year_month=curr_year_month)
    petition.month_records.add(month_record)
    # if months_agency:
    #     # last_pet_mon = pet_months.latest('month_agency__year_month')
    #     last_month_record = months_agency.latest('year_month')
    #     last_month = last_month_record.year_month if last_month_record else '2015-00'
    #     print("last_month: ", last_month)
    # else:
    #     print("NO ENCUENTRO NADA EN pet_months")
    #     last_month = '2015-00'
    #
    # between_months = month_records.filter(
    #     year_month__gt=last_month, year_month__lt=curr_year_month)
    # if not between_months:
    #     print("NO HAY NADA ENMEDIO", petition)
    #     prev_month = month_records.filter(
    #         year_month__lt=curr_year_month).latest()
    #     petition.month_records.add(prev_month)
    #     # PetitionMonth.objects.get_or_create(
    #     #     petition=petition, month_record=prev_month)
    # else:
    #     for mon_ent in between_months:
    #         petition.month_records.add(mon_ent)
    #         # PetitionMonth.objects.get_or_create(
    #         #     petition=petition, month_record=mon_ent)
    # print("Final:", petition.month_records.all().count())


def insert_from_json(
        all_array, columns, main_app, main_model, main_key, 
        special_functions=None):
    from django.apps import apps
    if not special_functions:
        special_functions = []
    agency_name_field = None
    agency_name_fields = [d for d in columns
                          if d.get('final_field', False) == "nombreSujetoObligado"]
    if agency_name_fields:
        agency_name_field = agency_name_fields[0].get("inai_open_search", False)
    for row in all_array:
        # from inai.models import Petition, ReplyFile
        from geo.models import Agency
        MainModel = apps.get_model(main_app, main_model)
        related_elem = None

        if "idSujetoObligado" in row:
            try:
                related_elem = Agency.objects.get(
                    idSujetoObligado=row["idSujetoObligado"])
            except Exception as e:
                print(e)
        if agency_name_field and not related_elem:
            # upper_inst = row["Institución"].replace("\r\n", "").strip().upper()
            upper_inst = row.get(agency_name_field, "").replace("\r\n", "").strip().upper()
            try:
                related_elem = Agency.objects.get(nombreSujetoObligado=upper_inst)
            except Agency.MultipleObjectsReturned:
                try:
                    related_elem = Agency.objects.get(
                        nombreSujetoObligado=upper_inst,
                        state__short_name=row["Estado o Federación"]
                    )
                except Exception as exc:
                    print("error también agregando estado", upper_inst)
                    print(exc)
            except Exception as e:
                print("Ningún elemento encontrado")
                print(e)
                print(upper_inst)
        if not related_elem:
            continue
        if not related_elem.nombreSujetoObligado:
            # related_elem.nombreSujetoObligado = row["nombreSujetoObligado"]
            related_elem.nombreSujetoObligado = row.get(agency_name_field, "")
            related_elem.save()
        main_columns = [d for d in columns
                        if d.get('model_name', False) == main_model]
        # unique_columns = [d for d in main_columns if d.get('unique', False)]
        unique_query = {
            Item["final_field"]: row.get(Item[main_key], related_elem)
            for Item in main_columns if Item.get('unique', False)}
        # list(filter(lambda d: d['unique'] in keyValList, exampleSet))
        try:
            main, created = MainModel.objects.get_or_create(**unique_query)
        except Exception as e:
            print(e)
            print(unique_query)
            raise e
        other_main_cols = [
            item for item in main_columns if not item.get('unique', False)]
        final_query = {}
        for col in other_main_cols:
            curr_value = row.get(col.get(main_key, "inai_open_search"), False)
            if curr_value:
                transform = col.get("transform", False)
                if transform:
                    curr_value = globals()[transform](curr_value, main)
                if final_field := col.get("final_field", False):
                    final_query[final_field] = curr_value

        main_obj = MainModel.objects.filter(id=main.id)
        main_obj.update(**final_query)
        main = main_obj.first()

        direct_transforms = [d for d in columns
                             if not d.get('model_name') and d.get('transform')]
        for col in direct_transforms:
            transform = col.get("transform")
            field = col.get(main_key, "inai_open_search")
            value = row.get(field, False)
            if value:
                globals()[transform](value, main)

        for function in special_functions:
            if created or function[1]:
                globals()[function[0]](row, main)


def recover_complain_data():
    from inai.models import Complaint
    for complaint in Complaint.objects.all():
        complaint.save_json_data(complaint.info_queja_inai)
