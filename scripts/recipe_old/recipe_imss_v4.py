# -*- coding: utf-8 -*-
import os

from django.conf import settings

import psycopg2

import unidecode
from django.utils import timezone

especialidad_medico_list = {}
type_document_list = {}
IMSS_ID = 3

dbname = "postgres"
user = "postgres"
password = "postgres"
host = "localhost"
port = 5432
constant_path = "C:\\git\\rick_\\Desktop\\nosotrxs\\issste\\"
script_dir = os.path.dirname(constant_path)
sep_cols = '|'
sep_rows = '\n'

data = ""
first_null = (
    "\n----------|------------------|-------------|---------------"
    "|--------------|--------------|---------------|-------------"
    "|-------------|-----------------|-----------------------"
    "|------------------|------------------|------------|-------------"
    "|-------------------|------------------|----")
year = '2019'
base_sql = (
    "COPY desabasto_recipereportraw(delegation,budget_key,"
    "unidad_medica,tipo_unidad_med,nivel_atencion,type_document,"
    "folio_document,date_release,fecha_entrega,clave_medicamento,"
    "descripcion_medicamento,prescribed_amount,delivered_amount,"
    "clave_doctor,nombre_medico,especialidad_medico,price,rn)")
base_sql2 = (
    "COPY desabasto_recipereportraw(delegation,budget_key,"
    "unidad_medica,tipo_unidad_med,nivel_atencion,type_document,"
    "folio_document,date_release,fecha_entrega,clave_medicamento,"
    "descripcion_medicamento,prescribed_amount,delivered_amount,"
    "clave_doctor,nombre_medico,especialidad_medico,price)")
options = "csv DELIMITER '|' NULL 'NULL' HEADER ENCODING 'LATIN1'"
options2 = "csv DELIMITER '|' NULL 'NULL' ENCODING 'LATIN1'"

catalog_document_type = {}
catalog_clues = {}
catalog_state = {}
claves_medico_dicc = {}
claves_medicamento = []
catalog_medical_speciality = {}
institution_obj = None
container_keys_list = []

data_file_medico = []
data_file_container = []
data_file_clues = []
data_file_error_rr = []

#Código original linux:
#split req_abril_2019_02.txt -d -l1000000 --additional-suffix=abril_2019_02
#RICK
clues_imss_prev = {}
clues_imss_after = {}
clues_imss_type = {}
clues_imss_name = {}
clues_imss_alone = {}


def split_file(path="G:/My Drive/YEEKO/Clientes/OCAMIS/imss"):
    from filesplit.split import Split
    curr_split = Split("%s/req_septiembre_2020_02.txt" % path, path)
    curr_split.bylinecount(linecount=1000000)

def massive_upload_csv_to_db(
        path="", years=['2019', '2020', '2021'], institution="imss",
        update_files=True):
    import os
    from formula.models import PrescriptionLog
    from catalog.models import Institution
    global institution_obj
    months = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
        "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    try:
        institution_obj = Institution.objects.get(code__iexact=institution)
        print("Procesando archivos para: ", institution_obj)
    except Institution.DoesNotExist:
        print("No existe la institution ", institution)
        return
    print("start process: ", timezone.now())
    for year in years:
        #for mon in range(12):
        for mon_idx, month in enumerate(months):
            base_path = "req_%s_%s_02" % (month, year)
            for file_num in range(99):
                rr_file_name = "%s_%s" % (base_path, file_num + 1)
                recipe_path = "recipe_imss_%s.csv" % (rr_file_name)
                medicine_path = "medicine_imss_%s.csv" % (rr_file_name)
                if path:
                    hash_dir = "" if path[-1] == "\\" else "\\"
                    reporte_recetas_path = "%s%s%s.txt" % (
                        path, hash_dir, rr_file_name)
                    recipe_path = "%s%s%s" % (path, hash_dir, recipe_path)
                    medicine_path = "%s%s%s" % (path, hash_dir, medicine_path)
                else:
                    reporte_recetas_path = "%s.txt" % rr_file_name
                if not os.path.exists(reporte_recetas_path):
                    # invalid path
                    print("Invalid path", rr_file_name)
                    break
                if not os.path.isfile(reporte_recetas_path):
                    # is not a file
                    print("Invalid path")
                    break
                if PrescriptionLog.objects.filter(
                        file_name=reporte_recetas_path,
                        successful=True).exists():
                    # previus successful processing
                    continue
                # se espera un resultado en este punto, pila de errores
                print(reporte_recetas_path)
                print("start converter_file_in_related_files: ",
                      timezone.now())
                year_month = "%s%s%s" % (
                    year, '0' if mon_idx < 10 else '', mon_idx)
                successful, errors = converter_file_in_related_files(
                    reporte_recetas_path, year_month=year_month,
                    institution=institution, recipe_path=recipe_path,
                    medicine_path=medicine_path, update_files=update_files)
                print("finish converter_file_in_related_files: ",
                      timezone.now())
                continue
                rr_log, is_created = PrescriptionLog.objects\
                    .get_or_create(file_name=reporte_recetas_path)
                rr_log.set_errors(errors)
                rr_log.successful = successful
                rr_log.save()
            else:
                continue
    print("end all process", timezone.now())


def get_data_from_file(reporte_recetas_path):
    import io
    try:
        with io.open(reporte_recetas_path, "r", encoding="latin-1") as file:
            data = file.read()
            file.close()
    except Exception as e:
        print(e)
        return False, ["%s" % (e)], False

    rr_data_rows = data.split("\n")

    return rr_data_rows, []


def get_type_document(type_document):
    """
    archivo local, si no existe, cargar los datos de db y generar el archivo
    si no existe type_document, generar un registro en db y actualiar el
    archivo retornar el type_document.id
    """
    from formula.models import DocumentType
    global catalog_document_type
    if not catalog_document_type:
        for document_type in DocumentType.objects.all():
            catalog_document_type[document_type.name] = document_type.id
    if type_document not in catalog_document_type:
        rr_document_type, is_created = DocumentType.objects\
            .get_or_create(name=type_document)
        catalog_document_type[type_document] = rr_document_type.id
    return catalog_document_type[type_document]


def get_state(state_name):
    from catalog.models import State

    try:
        state_name = unidecode.unidecode(state_name).upper()
    except Exception:
        state_name = state_name.upper()
    global catalog_state
    if not catalog_state:
        for state in State.objects.all():
            try:
                state.name = unidecode.unidecode(state.name).upper()
            except Exception:
                state.name = state.name.upper()
            catalog_state[state.name] = state

    if state_name not in catalog_state:
        state_obj = State.objects.create(inegi_code="xx", name=state_name)
        catalog_state[state_name] = state_obj

    return catalog_state[state_name]


#def get_clues_id(delegation, unidad_medica, tipo_unidad_med, institution):
def get_clues_id(entidad, unidad_medica, institution):

    from scripts.common import similar
    import re

    """
    cargar los datos basicos de todos los Clues pertenecientes a
    la institucion dada
    """
    global catalog_clues
    global data_file_clues
    global institution_obj

    #RICK
    global clues_imss_prev
    global clues_imss_after
    global clues_imss_type
    global clues_imss_name
    global clues_imss_alone

    try:
        unidad_medica = unidecode.unidecode(unidad_medica).upper()
    except Exception:
        unidad_medica = unidad_medica.upper()

    re_numbs = re.compile(r'^(\D+)(\d{1,3})\s?(.+)$')
    final_name = re.sub(re_numbs, '\\1|\\2|\\3', unidad_medica)
    splited = final_name.split("|")
    prev = splited[0].strip()
    if len(splited) == 1:
        if not prev:
            print("NO HAY PREVIO")
            print(splited)
            pass
        elif prev in clues_imss_alone:
            clues_imss_alone[prev] += 1
        else:
            clues_imss_alone[prev] = 1
    elif len(splited) == 3:
        numb = int(splited[1])
        after = splited[2].strip()
        re_consul = re.compile(
            r'(.+)\s(CONSULTA MEDICINA FAMILIAR|CONSULTA DE ESPECIALIDADES'
            r'|CONSULTA DENTAL|ATENCION MEDICA CONTINUA|HOSPITALIZACION'
            r'|SERVICIOS DE MEDICINA PREVENTI|CONSULTA DE MEDICINA FAMILIAR'
            r'|MODULOS FOMENTO SALUD|ADMISION CONTINUA|QUIROFANOS'
            r'|ATENCION MED CONTI|TERAPIA INTENSIVA|CONSMEDFAMILIAR'
            r'|CONS ESPECIALI|CONSULTORIO DENTAL|SALUD MATERNO INFANTIL'
            r'|CONSULTORIO SERVIC MEDICO EXTERNA)')
        final_name = re.sub(re_consul, '\\1|\\2', after)
        splited = final_name.split("|")
        name_clinic = None
        type_clinic = after
        if len(splited) == 2:
            name_clinic = splited[0]
            type_clinic = splited[1]
        if type_clinic in clues_imss_type:
            clues_imss_type[type_clinic] += 1
        else:
            clues_imss_type[type_clinic] = 1
        if name_clinic:
            if name_clinic in clues_imss_name:
                clues_imss_name[name_clinic] += 1
            else:
                clues_imss_name[name_clinic] = 1
        if after in clues_imss_after:
            clues_imss_after[after] += 1
        else:
            clues_imss_after[after] = 1

        if not prev:
            print("NO HAY PREVIO")
            print(splited)
            pass
        else:
            re_no_point = re.compile(r'(\s[NO|MF].?)$')
            prev = re.sub(re_no_point, '', prev)
            if prev in clues_imss_prev:
                clues_imss_prev[prev] += 1
            else:
                clues_imss_prev[prev] = 1
    else:
        print("!! hay un número raro de datos:")
        print(splited)
    return "algo"

    """for case in case_tests:
        print(case)
        final_name = re.sub(re_numbs, '\\1|\\2|\\3', case)
        splited = final_name.split("|")
        print(splited)"""


    from catalog.models import CLUES
    if not catalog_clues:
        institution_upper = institution.upper()
        clues_data_query = list(
            CLUES.objects.filter(
                institution__code=institution_upper)
            .values_list(
                "state__name", "name", "typology_cve",
                "id", "alternative_names"
            )
        )
        for clues_data in clues_data_query:
            cves = clues_data[2].split("/")
            for cve in cves:
                try:
                    clues_name = unidecode.unidecode(clues_data[1])
                except Exception:
                    clues_name = clues_data[1]
                prov_name = "%s %s" % (cve, clues_name)
                real_name = unidecode.unidecode(prov_name).upper()
                state_name = clues_data[0]
                builded_name = "%s$%s" % (real_name, state_name)
                if real_name not in catalog_clues:
                    catalog_clues[real_name] = [clues_data]
                else:
                    catalog_clues[real_name].append(clues_data)
            alt_names = clues_data[4]
            if alt_names:
                for alt_name in clues_data[4]:
                    if alt_name not in catalog_clues:
                        catalog_clues[alt_name] = [clues_data]
                    else:
                        catalog_clues[alt_name].append(clues_data)

    try:
        unidad_medica = unidecode.unidecode(unidad_medica).upper()
    except Exception:
        unidad_medica = unidad_medica.upper()

    # busqueda directa en mayúsculas
    clues = catalog_clues.get(unidad_medica)

    # if clues:
    #    print ("---> %s" % unidad_medica)

    if not clues:
        # print (unidad_medica)

        # busqueda por similar con valor de mas de .9 ------------------------
        similar_clues = []
        for clues_name in catalog_clues:
            similar_value = similar(clues_name, unidad_medica)
            if similar_value > 0.9:
                similar_clues.append([clues_name, similar_value])
        if similar_clues:
            def get_similar_value(similar_data):
                return similar_data[1]
            similar_clues.sort(key=get_similar_value, reverse=True)
            clues = catalog_clues[similar_clues[0][0]]
            catalog_clues[unidad_medica] = clues
            try:
                clues_obj = CLUES.objects.get(id=clues[0][3])
                alt_names = clues_obj.alternative_names
                if alt_names:
                    alt_names.append(unidad_medica)
                    clues_obj.alternative_names = alt_names
                    print("más de una alternativa:")
                    print(clues[0][3])
                else:
                    clues_obj.alternative_names = [unidad_medica]
                clues_obj.save()
            except:
                print("no se contempló el artificial_id:")
                print(clues[0][3])

    if not clues:
        # print ("---------")
        # no se encontro por busqueda directa ni por similar, registro nuevo
        # metodo 2 registro por csv con ids calculados
        if not data_file_clues:
            # calcular el ultimo id para colocar ids artificiales:
            last_clues_id = CLUES.objects.values_list("id", flat=True)\
                .order_by("id").last() or 1
        else:
            last_clues_id = data_file_clues[-1][0]
        artificial_id = last_clues_id + 1
        state = get_state(entidad)
        data_file_clues.append([
            artificial_id,
            state.id,
            institution_obj.id,
            unidad_medica,
            0,
            "xx",
            "unknown",
            "unknown",
            "unknown",
            "unknown",
            "unknown",
            "unknown",
            "unknown",
            "unknown",
            "unknown",
            "unk",
            "unknown",
            "unkn",
            "unknown",
            0, 0, 0, 0, 0,
            "unknown",
            "unknown",
            "unknown",
            0
        ])
        #print(len(data_file_clues))

        clues = [[state.name, unidad_medica, "unknown", artificial_id, None]]
        catalog_clues[unidad_medica] = clues
        return artificial_id
    else:
        return clues[0][3]


def check_clave_medicamento(clave_medicamento, descripcion_medicamento):
    # la busqueda de existencia de medicamentos se basara en Container.key2
    # se eliminaran los "." de la clave para tener algo mas estandar y se usara
    # el enfoque de cargar la lista de todos los key2 en db, generar el archivo
    # para los que no existan
    from medicine.models import Container
    global claves_medicamento
    clave_medicamento = clave_medicamento.replace(".", "")
    if not claves_medicamento:
        claves_medicamento = list(
            Container.objects.all().values_list("key2", flat=True).distinct())
    if clave_medicamento not in claves_medicamento:
        clave_medicamento_full = clave_medicamento  # agregar puntos
        data_file_container.append([clave_medicamento_full,
                                    clave_medicamento,
                                    descripcion_medicamento])
        claves_medicamento.append(clave_medicamento)


def get_especialidad_medico_id(especialidad_medico):
    from formula.models import MedicalSpeciality
    global catalog_medical_speciality

    try:
        especialidad_medico = unidecode.unidecode(especialidad_medico).upper()
    except Exception:
        especialidad_medico = especialidad_medico.upper()
    if not catalog_medical_speciality:
        catalog_medical_speciality = {
            obj.name: obj.id for obj in MedicalSpeciality.objects.all()
        }
    if especialidad_medico not in catalog_medical_speciality:
        medical_sp_obj, is_created = MedicalSpeciality.objects\
            .get_or_create(name=especialidad_medico)
        catalog_medical_speciality[especialidad_medico] = medical_sp_obj.id
    return catalog_medical_speciality[especialidad_medico]


def check_clave_doctor(clave_doctor, nombre_medico, especialidad_medico):
    from formula.models import Doctor
    global data_file_medico
    global claves_medico_dicc
    if not claves_medico_dicc:
        claves_medico = list(
            Doctor.objects.values_list("clave_doctor", flat=True))
        claves_medico_dicc = {}
        for clave in claves_medico:
            claves_medico_dicc[clave] = True
    if clave_doctor not in claves_medico_dicc and clave_doctor != 1000000000:
        claves_medico_dicc[clave_doctor] = True
        data_file_medico.append([
            clave_doctor, nombre_medico,
            get_especialidad_medico_id(especialidad_medico)])
        # agregar al medico al archivo para generar medico


#Divide toda una fila en columnas
def divide_recipe_report_data(
        text_data, control_parameter=None, file=None, row_seq=None):
    recipe_report_data = text_data.split("|")
    rr_data_count = len(recipe_report_data)
    #Comprobación del número de columnas
    from inai.models import NameColumn
    #from formula.models import MissingRow
    current_columns = NameColumn.objects.filter(
        file_control__controlparameters=control_parameter)
    columns_count = current_columns.filter(
        position_in_data__isnull=False).count()
    if rr_data_count == columns_count:
    #if rr_data_count == 14:
        return recipe_report_data
    else:
        MissingRow.objects.create()
        print("conteo extraño: %s columnas" % rr_data_count)
        print(recipe_report_data)
    return None


def get_recipe_report_data(recipe_report_data, institution="issste"):
    entidad = recipe_report_data[0]
    unidad_medica = recipe_report_data[1]
    nivel_atencion = recipe_report_data[2]


    #clues_id = get_clues_id(
    #    delegation, unidad_medica, tipo_unidad_med, institution)
    clues_id = get_clues_id(entidad, unidad_medica, institution)
    return [
        clues_id,
        "--",
        "--",
        "--",
        "--",
    ]
    if not clues_id or clues_id == "":
        print(recipe_report_data)
    #clues_id = 0


    type_document_id = get_type_document(recipe_report_data[5])
    #type_document_id = 0

    fecha_entrega = recipe_report_data[8]

    # ###revicion de existencia de clave_doctor
    clave_doctor = recipe_report_data[13]
    nombre_medico = recipe_report_data[14]
    especialidad_medico = recipe_report_data[15]
    clave_doctor = clave_doctor if not clave_doctor == "NULL" else 1000000000
    nombre_medico = nombre_medico if not nombre_medico == "NULL" else "unknown"
    especialidad_medico = (especialidad_medico
                           if not especialidad_medico == "NULL"
                           else "unknown")
    check_clave_doctor(clave_doctor, nombre_medico, especialidad_medico)

    return [
        clues_id,
        type_document_id,
        fecha_entrega,
        nivel_atencion,
        clave_doctor,
    ]


def get_recipe_medicine_data(recipe_report_data):
    clave_medicamento = recipe_report_data[9]
    descripcion_medicamento = recipe_report_data[10]
    check_clave_medicamento(clave_medicamento, descripcion_medicamento)

    # ###revicion de existencia de clave_medicamento

    prescribed_amount = recipe_report_data[11]
    delivered_amount = recipe_report_data[12]
    price = recipe_report_data[16]
    rn = recipe_report_data[17]
    # convertir datos a enteros
    calculate_delivered = True
    if (prescribed_amount or "").isdigit():
        prescribed_amount = int(prescribed_amount)
    else:
        calculate_delivered = False
        prescribed_amount = "NULL"

    #
    if (delivered_amount or "").isdigit():
        delivered_amount = int(delivered_amount)
    else:
        calculate_delivered = False
        delivered_amount = "NULL"
    # ---------------------------
    if calculate_delivered:
        # calculo de delivered
        if delivered_amount:
            if prescribed_amount == delivered_amount:
                delivered_type = "all"
            else:
                delivered_type = "ptl"
        else:
            delivered_type = "no"
    else:
        delivered_type = "NULL"

    return [
        clave_medicamento,
        prescribed_amount,
        delivered_amount,
        price,
        delivered_type,
        rn,
    ]


def converter_file_in_related_files(
        reporte_recetas_path, year_month=0, institution="issste",
        update_files=True,
        recipe_path="test_recipe.csv", medicine_path="test_medicine.csv",
        medico_path="test_medico.csv", clues_path="test_clues.csv",
        container_path="test_container.csv"):
    from formula.models import Prescription
    from datetime import datetime
    from pprint import pprint
    #import io
    rr_data_rows, errors = get_data_from_file(reporte_recetas_path)
    if errors:
        return False, errors

    data_file_recipe = []
    data_file_medicine = []

    global data_file_medico
    global data_file_container
    global data_file_clues
    global data_file_error_rr
    data_file_medico = []
    data_file_container = []
    data_file_clues = []

    # -----------------------------------------------------
    # revisión de la existencia del primer folio ----------
    # Comprobación de la primera fila como encabezado
    recipe_first = rr_data_rows[0].split("|")
    recipes_data = {}

    if len(recipe_first) >= 14:
        first_folio = recipe_first[4]
        previus_recipe = Prescription.objects\
            .filter(folio_document=first_folio).first()
        if previus_recipe:
            recipes_data[first_folio] = {
                "id": first_folio,
                "medicines": [],
                "exist": True,
                "delivered_medicine": [previus_recipe.delivered]
            }
    # -----------------------------------------------------

    print("start for rr_data_rows: ", timezone.now())
    # for rr_data_row in rr_data_rows:
    last_date = None
    iso_date = None
    first_iso = None
    for idx, rr_data_row in enumerate(rr_data_rows):
        if idx % 100000 == 0:
            print("idx: %s" % idx, timezone.now())
        # rr_data_row = rr_data_row.decode('latin-1').encode("utf-8")
        # rr_data_row = rr_data_row.encode("utf-8")
        recipe_report_prev_data = divide_recipe_report_data(
            rr_data_row, row_seq=idx)
        if not recipe_report_prev_data:
            continue

        folio_document = recipe_report_prev_data[4]
        date_release = recipe_report_prev_data[6]

        if last_date != date_release:
            last_date = date_release
            #Cálculo de la semana epidemiológica:
            try:
                curr_date = datetime.strptime(last_date, '%d/%m/%Y')
                iso_date = curr_date.isocalendar()
                if not first_iso:
                    first_iso = iso_date
            except Exception as e:
                print(e)
                print(last_date)
                print(recipe_report_prev_data)
                continue

        folio_ocamis = "%s-%s-%s" % (iso_date[0], iso_date[1], folio_document)

        if folio_ocamis not in recipes_data:
            recipes_data[folio_ocamis] = True
            
            recipe_report_data = get_recipe_report_data(
                recipe_report_prev_data, institution)
            """(clues_id,
             type_document_id,
             fecha_entrega,
             nivel_atencion,
             clave_doctor) = recipe_report_data

            recipes_data[folio_ocamis] = {
                "clues_id": clues_id,
                "folio_ocamis": folio_ocamis,
                "type_document_id": type_document_id,
                "folio_document": folio_document,
                "iso_year": iso_date[0],
                "iso_week": iso_date[1],
                "iso_day": iso_date[2],
                "date_release": date_release,
                "fecha_entrega": fecha_entrega,
                "nivel_atencion": nivel_atencion,
                "clave_doctor": clave_doctor,
                "delivered_medicine": [],
                "year_month": year_month
            }"""
        continue

        recipe_medicine_data = get_recipe_medicine_data(
            recipe_report_prev_data)

        (clave_medicamento,
         prescribed_amount,
         delivered_amount,
         price,
         delivered_type,
         rn) = recipe_medicine_data

        recipes_data[folio_ocamis]["delivered_medicine"]\
            .append(delivered_type)

        data_file_medicine.append([
            folio_ocamis,
            clave_medicamento,
            prescribed_amount,
            delivered_amount,
            price,
            rn,
            delivered_type
        ])

    print("clues_imss_prev")
    pprint(clues_imss_prev)
    print("clues_imss_after")
    pprint(clues_imss_after)
    print("clues_imss_type")
    pprint(clues_imss_type)
    print("clues_imss_name")
    pprint(clues_imss_name)
    print("clues_imss_alone")
    pprint(clues_imss_alone)
    

    return True, False
    
    print("finish for rr_data_rows: ", timezone.now())
    # creacion del archivo de folios apartir del recipes_data
    #folios_list = sorted([folio for folio in recipes_data])
    #folio_lt = folios_list[0]
    #folio_gt = folios_list[-1]

    range_folios = list(
        Prescription.objects
        .filter(iso_year=first_iso[0], iso_week=first_iso[1])
        .values_list("folio_ocamis", flat=True))

    range_folios_dicc = {}
    for fol in range_folios:
        range_folios_dicc[fol] = True
    exists_folios = []

    print("start for recipes_data: ", timezone.now())
    for folio_ocami, recipe_data in recipes_data.items():
        folio_ocamis = recipe_data.get("folio_ocamis")
        if not folio_ocamis:
            continue

        delivered_medicine = recipe_data.get("delivered_medicine")
        if not delivered_medicine:
            recipe_delivered = "NULL"
        else:
            if all([delivered == "all" for delivered in delivered_medicine]):
                recipe_delivered = "all"
            elif all([delivered == "no" for delivered in delivered_medicine]):
                recipe_delivered = "no"
            else:
                recipe_delivered = "ptl"

        if folio_ocamis in range_folios_dicc:
            exists_folios.append([folio_ocamis, recipe_delivered])
            # si ya existe, deverimos actualizar su recipe_delivered?
            print(folio_ocamis)
            continue

        data_file_recipe.append([
            recipe_data.get("clues_id"),
            folio_ocamis,
            recipe_data.get("type_document_id"),
            recipe_data.get("folio_document"),
            recipe_data.get("iso_year"),
            recipe_data.get("iso_week"),
            recipe_data.get("iso_day"),
            recipe_data.get("date_release"),
            recipe_data.get("fecha_entrega"),
            recipe_data.get("nivel_atencion"),
            recipe_data.get("clave_doctor"),
            recipe_delivered,
            year_month])
    # ordenado por folio_document
    print("start sort:", timezone.now())
    data_file_recipe.sort(key=lambda x: x[1])

    print("finish for recipes_data: ", timezone.now())
    print("se termino de calcular los objetos recipe")

    # Creacion de los archivos CSV
    import csv

    update_configs = [
        {
            "path": clues_path,
            "fields": [
                "id", "state_id", "institution_id", "name", "is_searchable",
                "municipality_inegi_code", "municipality", "typology",
                "typology_cve", "id_clues", "clues", "status_operation",
                "longitude", "latitude", "locality", "locality_inegi_code",
                "jurisdiction", "jurisdiction_clave", "establishment_type",
                "consultings_general", "consultings_other", "beds_hopital",
                "beds_other", "total_unities", "admin_institution",
                "atention_level", "stratum", "is_national"
            ],
            "table_name": "desabasto_clues",
            "data_file": data_file_clues,
        },
        {
            "path": medico_path,
            "fields": [
                "clave_doctor", "nombre_medico", "especialidad_medico_id"
            ],
            "table_name": "desabasto_medic",
            "data_file": data_file_medico,
        },
        {
            "path": container_path,
            "fields": ["key", "key2", "name"],
            "table_name": "desabasto_container",
            "data_file": data_file_container,
        },
        {
            "path": recipe_path,
            "fields": [
                "clues_id",
                "folio_ocamis",
                "type_document_id",
                "folio_document",
                "iso_year",
                "iso_week",
                "iso_day",
                "date_release",
                "fecha_entrega",
                "nivel_atencion",
                "medico_id",
                "delivered",
                "year_month",
            ],
            "table_name": "desabasto_recipereport2",
            "data_file": data_file_recipe,
        },
        {
            "path": medicine_path,
            "fields": [
                "recipe_id",
                "clave_medicamento",
                "prescribed_amount",
                "delivered_amount",
                "price",
                "rn",
                "delivered"
            ],
            "table_name": "desabasto_recipemedicine2",
            "data_file": data_file_medicine,
        }]

    print(data_file_recipe[0])
    for update_config in update_configs:
        csv_path = update_config.get("path")
        data_file = update_config.get("data_file")
        print(csv_path)
        print(True if data_file else False)
        #with open(csv_path, 'wb', encoding="latin-1") as csv_file:
        #with open(csv_path, 'r', encoding="latin-1") as csv_file:
        with open(csv_path, 'w', encoding="latin-1", newline="") as csv_file:
            write = csv.writer(csv_file, delimiter='|')
            write.writerows(data_file)
            csv_file.close()

    if update_files:
        for update_config in update_configs:
            upload_csv_to_database(
                update_config.get("path"),
                update_config.get("table_name"),
                update_config.get("fields"),
            )
    return True, False


def special_coma(all_data):
    rows = all_data.split("\n")
    count = 0
    final_rows = []
    for idx, row in enumerate(rows):
        new_row = row.replace('1,114 gr.', '1$114 gr.')\
            .replace('0,000', '0$000').replace('VERACRUZ,VER', 'VERACRUZ$VER')\
            .replace(' VEGA,CULIAC', 'VEGA$CULIAC')\
            .replace(' PUCHADES,TEPIC', 'PUCHADES$TEPIC')
        cols = new_row.split(",")
        len_cols = len(cols)
        if len_cols == 17:
            final_rows.append(sep_cols.join(cols).replace('$', ","))
        elif len_cols > 17:
            new_row = new_row.replace(
                ',',
                '|').replace(
                '| ',
                ', ').replace(
                '$',
                ",")
            cols = new_row.split(sep_cols)
            len_cols = len(cols)
            if len_cols == 16:
                clave = cols[13].replace(', ', ',').split(",")
                cols = sep_cols.join(cols[:13] + clave + cols[14:])
                final_rows.append(cols)
            elif len_cols == 17:
                final_rows.append(new_row)
            elif len_cols > 17:
                count += 1
                if count < 20:
                    print("--------------------")
                    print("error 1")
                    print(idx)
                    print(row)
                    # break
                # print (new_row)
                # for col in cols:
                #    print (col)
            else:
                count += 1
                print("error 2")
                print(row)
                # break
        else:
            print("error 3")
            print(row)
            break
    print("especial coma %s errores" % count)
    all_data = sep_rows.join(final_rows)
    return all_data


def special_excel(all_data):
    import re
    rows = all_data.split("\n")
    final_rows = []
    for row in rows:
        new_row = re.sub(r'(\,)+$', r'', row)
        final_rows.append(new_row)
    all_data = sep_rows.join(final_rows)
    return all_data


def clean_special(data):
    message_final = 'sys.databases\n'
    idx_col = 0
    while True:
        try:
            idx_col = data.index('COLECTIVO|', idx_col + 80)
            idx_year = data.index("|%s" % year, idx_col, idx_col + 80)
            if "|" in data[idx_col + 10:idx_year]:
                print("hay un espacio de mas")
                curr_str = data[idx_col + 10:idx_year - 1]
                print(curr_str)
                curr_done = curr_str.replace("|", "-")
                next_data = data[idx_col:idx_col + 6000]
                cleaned_current = next_data.replace(curr_str, curr_done)
                data = "%s%s%s" % (
                    data[:idx_col], cleaned_current, data[idx_col + 6000:])
            else:
                pass
        except Exception:
            break
    while True:
        try:
            idx_msg = data.index('Mensaje 9002')
            idx_msg2 = data.index(message_final, idx_msg)
            print("----------")
            print(data[idx_msg:idx_msg2 + len(message_final)])
            data = "%s%s" % (data[:idx_msg],
                             data[idx_msg2 + len(message_final):])
        except Exception:
            break
    fabian = 'FABIAN ZARATE GALINDO|'
    fabian2 = 'FABIAN ZARATE GALINDO||'
    if fabian2 in data:
        print("caso FABIAN")
        data = data.replace(fabian2, fabian)
    return data


def upload_csv_to_database(file_path, table_name, columns):
    f = open(file_path)
    import os
    base_dir = os.path.dirname(os.path.dirname(__file__))

    columns_join = ",".join(columns)
    options = "csv DELIMITER '|' NULL 'NULL' ENCODING 'LATIN1'"
    sql = "COPY %s(%s) FROM '%s\\%s' %s;" % (
        table_name, columns_join, base_dir, file_path, options)

    desabasto_conection = getattr(settings, "DATABASES").get("default")
    con = psycopg2.connect(
        database=desabasto_conection.get("NAME"),
        user=desabasto_conection.get("USER"),
        password=desabasto_conection.get("PASSWORD"),
        host=desabasto_conection.get("HOST"),
        port=desabasto_conection.get("PORT"))
    cur = con.cursor()
    try:
        cur.copy_expert(sql, f)
        # with open("%s_done" % file_path, 'wb') as file:
        #     file.write('done')
        # os.remove("%s\\%s" % (script_dir, origin_path))
    except Exception as e:
        print(e)
        con.close()
        f.close()
        return
    con.commit()
    con.close()
    f.close()
