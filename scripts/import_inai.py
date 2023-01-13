others: [
    {
        "inai_open_search": "archivoAdjuntoRespuesta",
        "app_name": "inai",
        "model_name": "ProcessFile",
        "final_field": "url_download",
        "transform": "join_url",
    },
    {
        "inai_open_search": "datosAdicionales",
        "app_name": "inai",
        "model_name": "Petition",
        "final_field": "description_petition",
        "transform": "join_lines",
        "join_lines": True
    }
]

def unescape(val):
    import html
    return html.unescape(val)

def date_mex(val):
    from datetime import datetime
    return datetime.strptime(val, '%d/%m/%Y')

def to_json(val):
    import json
    return json.loads(val)

def get_status_obj(val):
    from category.models import StatusControl
    return StatusControl.objects.get(public_name=val, group="petition")


def join_url(row, main):
    from inai.models import ProcessFile
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
            ProcessFile.objects.get_or_create(
                petition=main, file_type=default_type, url_download=final_url)
        except Exception as e:
            print("No se pudo crear el archivo")
            print(e)
        #main.update()


def add_limit_complain(row, main):
    from inai.models import ProcessFile, PetitionBreak
    from category.models import DateBreak

    try:
        default_break = DateBreak.objects.get(name="response_limit")
    except Exception as e:
        print("No se encontró el tipo de archivo")
        print(e)
        return
    final_date = date_mex(row["Fecha límite de entrega"])
    try:
        petition_break, created_pb = PetitionBreak.objects.get_or_create(
            petition=main, date_break=default_break)
        petition_break.date = final_date
        petition_break.save()
    except Exception as e:
        print("No se pudo crear la fecha")
        print(e)
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
    from inai.models import MonthEntity, PetitionMonth
    #print(petition.send_petition)
    month = petition.send_petition.month
    year = petition.send_petition.year
    curr_month = "%s%s%s" % (year, '0' if month < 10 else '', month)
    pet_months = PetitionMonth.objects.filter(petition__entity=petition.entity)
    print("-------------")
    print("curr_month: ", curr_month)
    if pet_months:
        last_pet_mon = pet_months.latest('month_entity__year_month')
        last_month = last_pet_mon.month_entity.year_month if last_pet_mon else '201500'
        print("last_month: ", last_month)
    else:
        print("NO ENCUENTRO NADA EN pet_months")
        last_month = '201500'
    month_entities = MonthEntity.objects.filter(entity=petition.entity)
    between_months = month_entities.filter(
        year_month__gt=last_month, year_month__lt=curr_month)
    if not between_months:
        print("NO HAY NADA ENMEDIO")
        prev_month = month_entities.filter(year_month__lt=curr_month).latest()
        PetitionMonth.objects.get_or_create(
            petition=petition, month_entity=prev_month)
    else:
        for mon_ent in between_months:
            PetitionMonth.objects.get_or_create(
                petition=petition, month_entity=mon_ent)
    pet_months2 = PetitionMonth.objects.filter(petition__entity=petition.entity)
    print("Final:")
    print(pet_months2.count())


def insert_from_json(
        all_array, columns, main_app, main_model, main_key, 
        special_functions=[]):
    from django.apps import apps
    for row in all_array:
        #from inai.models import Petition, ProcessFile
        from catalog.models import Entity
        MainModel = apps.get_model(main_app, main_model)
        related_elem = None
        try:
            related_elem = Entity.objects.get(
                idSujetoObligado=row["idSujetoObligado"])
        except Exception as e:
            print(e)
        try:
            related_elem = Entity.objects.get(
                nombreSujetoObligado=row["Institución"].upper())
        except Exception as e:
            print(e)
        if not related_elem:
            continue
        if not related_elem.nombreSujetoObligado:
            related_elem.nombreSujetoObligado = row["nombreSujetoObligado"]
            related_elem.save()
        main_columns = [d for d in columns 
            if d.get('model_name', False) == main_model]
        #unique_columns = [d for d in main_columns if d.get('unique', False)]
        unique_query = {
            #Item["final_field"]:row.get(Item[main_key], related_elem)
            #    for Item in unique_columns }
            Item["final_field"]: row.get(Item[main_key], related_elem)
                for Item in main_columns if Item.get('unique', False)}
        #list(filter(lambda d: d['unique'] in keyValList, exampleSet))
        try:
            main, created = MainModel.objects.get_or_create(**unique_query)
        except Exception as e:
            print(e)
            raise e
        other_cols = [
            item for item in main_columns if not item.get('unique', False)]
        final_query = {}
        for col in other_cols:
            curr_value = row.get(col[main_key], False)
            if curr_value:
                transform = col.get("transform", False)
                if transform:
                    curr_value = globals()[transform](curr_value)
                final_query[col["final_field"]] = curr_value
        main_obj = MainModel.objects.filter(id=main.id)
        main_obj.update(**final_query)
        main = main_obj.first()
        for function in special_functions:
            if (created or function[1]):
                globals()[function[0]](row, main)

