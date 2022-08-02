inai_fields = [
    {
        "inai_open_search": "idSujetoObligado",
        "model_name": "Entity",
        "app_name": "catalog",
        "final_field": "idSujetoObligado",
        "related": 'entity',
    },
    {
        "inai_open_search": "nombreSujetoObligado",
        "model_name": "Entity",
        "app_name": "catalog",
        "final_field": "nombreSujetoObligado",
        "insert": True,
        "related": 'entity',
    },
    {
        "inai_open_search": "dsFolio",
        "app_name": "inai",
        "model_name": "Petition",
        "final_field": "folio_petition",
        "unique": True,
    },
    {
        "inai_open_search": False,
        "app_name": "inai",
        "model_name": "Petition",
        "final_field": "entity",
        "unique": True,
    },
    {
        "inai_open_search": "descripcionSolicitud",
        "app_name": "inai",
        "model_name": "Petition",
        "final_field": "description_petition",
        "transform": "unescape",
    },
    {
        "inai_open_search": "fechaEnvio",
        "app_name": "inai",
        "model_name": "Petition",
        "final_field": "send_petition",
        "transform": "date_mex",
    },
    {
        "inai_open_search": "descripcionRespuesta",
        "app_name": "inai",
        "model_name": "Petition",
        "final_field": "description_response",
        "transform": "unescape",
    },
    {
        "inai_open_search": "dtFechaUltimaRespuesta",
        "app_name": "inai",
        "model_name": "Petition",
        "final_field": "send_response",
        "transform": "date_mex",
    },
    {
        "inai_open_search": "id",
        "app_name": "inai",
        "model_name": "Petition",
        "final_field": "id_inai_open_data",
    },
    {
        "inai_open_search": "informacionQueja",
        "app_name": "inai",
        "model_name": "Petition",
        "final_field": "info_queja_inai",
        "transform": "to_json",
    },

]

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
    }]



import io
import json
from pprint import pprint
from django.apps import apps
from datetime import datetime

data = None
path_json = "C:\\Users\\Ricardo\\Desktop\\experimentos\\todas.json"

with io.open(path_json, "r", encoding="UTF-8") as file:
    data = json.load(file)
    file.close()

petitions = data["solicitudes"]
#petitions = [pet for pet in data["solicitudes"] if pet["idSujetoObligado"] ==  15233]

for pet in petitions:
    val = pet["fechaEnvio"]
    pet["fecha_orden"] = datetime.strptime(val, '%d/%m/%Y')

petitions = sorted(petitions, key=lambda i: i['fecha_orden'])
#for pet in petitions:
#    print(pet["fechaEnvio"])





def unescape(val):
    import html
    return html.unescape(val)

def date_mex(val):
    return datetime.strptime(val, '%d/%m/%Y')

def to_json(val):
    import json
    return json.loads(val)


def join_url(row, main):
    from inai.models import ProcessFile
    from category.models import FileType
    default_url = "https://descarga.plataformadetransparencia.org.mx/buscador-ws/descargaArchivo/SISAI/"
    compl_hash = row.get("archivoAdjuntoRespuesta", False)
    if compl_hash:
        try:
            default_type = FileType.objects.get(name="Información no final")
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


def join_lines(row, main):
    from inai.models import Petition
    curr_value = row.get("datosAdicionales", False)
    if curr_value:
        curr_value = main.description_petition + "\n\n--------------\n\n" + curr_value
        main_obj = Petition.objects.filter(id=main.id)
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
    for row in all_array:
        #from inai.models import Petition, ProcessFile
        from catalog.models import Entity
        MainModel = apps.get_model(main_app, main_model)
        try:
            related_elem = Entity.objects.get(
                idSujetoObligado=row["idSujetoObligado"])
        except Exception as e:
            print(e)
        if not related_elem.nombreSujetoObligado:
            related_elem.nombreSujetoObligado = row["nombreSujetoObligado"]
            related_elem.save()
        main_columns = [d for d in columns 
            if d.get('model_name', False) == main_model]
        unique_columns = [d for d in main_columns if d.get('unique', False)]
        unique_query = {
            Item["final_field"]:row.get(Item[main_key], related_elem)
                for Item in unique_columns }
        #list(filter(lambda d: d['unique'] in keyValList, exampleSet))
        try:
            main, created = MainModel.objects.get_or_create(**unique_query)
        except Exception as e:
            print(e)
            raise e
        other_cols = [d for d in main_columns if not d.get('unique', False)]
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
            globals()[function](row, main)


def execute():
    spec_functions = ["join_url", "join_lines", "insert_between_months"]
    insert_from_json(
        petitions, inai_fields, 'inai', 'Petition', 'inai_open_search', 
        special_functions=spec_functions)



def delete_pets():
    from inai.models import Petition
    Petition.objects.all().delete()


    #Petition.objects.last()
