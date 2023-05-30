
def unescape(val, petition):
    import html
    return html.unescape(val)


def add_br(val, petition):
    return val.replace("\n", "<br>")


def date_mex(val, petition):
    from datetime import datetime
    try:
        return datetime.strptime(val, "%d/%m/%Y")
    except Exception as e:
        print("Error en la fecha: ", val)
        print(e)
        return None


def to_json(val, petition):
    import json
    return json.loads(val)


def get_status_obj(val, petition):
    from category.models import StatusControl, InvalidReason
    status_found = None
    try:
        status_found = StatusControl.objects.get(public_name=val, group="petition")
    except StatusControl.DoesNotExist:
        pass
    if not status_found:
        try:
            status_found = StatusControl.objects.get(addl_params__icontains=val, group="petition")
        except StatusControl.DoesNotExist:
            print("No encontramos el status: ", val)
    if val == "Desechada por falta de respuesta del ciudadano":
        invalid_reason = InvalidReason.objects.get(name="Desechada")
        petition.invalid_reason = invalid_reason
        petition.save()
    if not status_found:
        return petition.status_petition
    elif not petition.status_petition:
        return status_found
    else:
        return petition.status_petition if petition.status_petition.order > status_found.order else status_found


def join_url(row, main):
    from inai.models import ReplyFile
    from category.models import FileType
    default_url = "https://descarga.plataformadetransparencia.org.mx/buscador-ws/descargaArchivo/SISAI/"
    compl_hash = row.get("archivoAdjuntoRespuesta", False)
    if compl_hash:
        try:
            default_type = FileType.objects.get(name="no_final_info")
        except Exception as e:
            print("No se encontró el tipo de archivo")
            print(e)
            return
        final_url = "%s%s" % (default_url, row["archivoAdjuntoRespuesta"])
        try:
            ReplyFile.objects.get_or_create(
                petition=main, file_type=default_type, url_download=final_url)
        except Exception as e:
            print("No se pudo crear el archivo")
            print(e)
        #main.update()


def add_limit_complain(row, main):
    from inai.models import ReplyFile, PetitionBreak
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

    #main.update()


def join_lines(row, main):
    from inai.models import Petition
    curr_value = row.get("datosAdicionales", False)
    if curr_value:
        curr_value = main.description_petition + "\n\n--------------\n\n" + curr_value
        main_obj = Petition.objects.filter(id=main.id)
        if main_obj[0].description_petition != curr_value:
            main_obj.update(description_petition=curr_value)


def insert_between_months(row, petition):
    from inai.models import EntityMonth
    #print(petition.send_petition)
    if petition.send_petition:
        month = petition.send_petition.month
        year = petition.send_petition.year
    else:
        month = 1
        year = 2018
    curr_year_month = f"{year}-{month:02d}"
    # pet_months = PetitionMonth.objects.filter(petition__agency=petition.agency)
    months_agency = petition.entity_months.all()
    print("-------------")
    print("curr_year_month: ", curr_year_month)
    if months_agency:
        # last_pet_mon = pet_months.latest('month_agency__year_month')
        last_entity_month = months_agency.latest('year_month')
        last_month = last_entity_month.year_month if last_entity_month else '2015-00'
        print("last_month: ", last_month)
    else:
        print("NO ENCUENTRO NADA EN pet_months")
        last_month = '2015-00'
    entity_months = EntityMonth.objects.filter(entity=petition.agency.entity)
    between_months = entity_months.filter(
        year_month__gt=last_month, year_month__lt=curr_year_month)
    if not between_months:
        print("NO HAY NADA ENMEDIO", petition)
        prev_month = entity_months.filter(
            year_month__lt=curr_year_month).latest()
        petition.entity_months.add(prev_month)
        # PetitionMonth.objects.get_or_create(
        #     petition=petition, entity_month=prev_month)
    else:
        for mon_ent in between_months:
            petition.entity_months.add(mon_ent)
            # PetitionMonth.objects.get_or_create(
            #     petition=petition, entity_month=mon_ent)
    print("Final:", petition.entity_months.all().count())


def insert_from_json(
        all_array, columns, main_app, main_model, main_key, 
        special_functions=[]):
    from django.apps import apps
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
        if "Institución" in row:
            upper_inst = row["Institución"].replace("\r\n", "").strip().upper()
            try:
                related_elem = Agency.objects.get(
                    nombreSujetoObligado=upper_inst)
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
            related_elem.nombreSujetoObligado = row["nombreSujetoObligado"]
            related_elem.save()
        main_columns = [d for d in columns
                        if d.get('model_name', False) == main_model]
        # unique_columns = [d for d in main_columns if d.get('unique', False)]
        unique_query = {
            # Item["final_field"]:row.get(Item[main_key], related_elem)
            #    for Item in unique_columns }
            Item["final_field"]: row.get(Item[main_key], related_elem)
            for Item in main_columns if Item.get('unique', False)}
        # list(filter(lambda d: d['unique'] in keyValList, exampleSet))
        try:
            main, created = MainModel.objects.get_or_create(**unique_query)
        except Exception as e:
            print(e)
            print(unique_query)
            raise e
        other_cols = [
            item for item in main_columns if not item.get('unique', False)]
        final_query = {}
        for col in other_cols:
            curr_value = row.get(col[main_key], False)
            if curr_value:
                transform = col.get("transform", False)
                if transform:
                    curr_value = globals()[transform](curr_value, main)
                final_query[col["final_field"]] = curr_value
        main_obj = MainModel.objects.filter(id=main.id)
        main_obj.update(**final_query)
        main = main_obj.first()
        for function in special_functions:
            if created or function[1]:
                globals()[function[0]](row, main)
