# -*- coding: utf-8 -*-
from rest_framework.response import Response
from rest_framework import permissions, views, status
import unidecode
from data_param.models import FinalField
from category.models import StatusControl

recipe_fields = FinalField.objects.filter(
    collection__model_name='Prescription').values()
droug_fields = FinalField.objects.filter(
    collection__model_name='Droug').values()
catalog_clues = {}
catalog_state = {}
catalog_delegation = {}
claves_medico_dicc = {}
columns = {}
institution = None
state = None


def start_file_process_prev(file, file_control, is_explore=False):
    from inai.models import File
    file.error_process = None
    file.save()
    first_file, count_splited, errors, suffix = split_and_decompress(file)
    if errors:
        file.save_errors(errors, 'initial_explore')
        return Response(
            {"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
    if count_splited and not is_explore:
        warnings = [("Son muchos archivos y tardarán en"
            " procesarse, espera por favor")]
        return Response(
            {"errors": warnings}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    if not is_explore:
        build_catalogs(file)
    if is_explore:
        data = transform_files_in_data(
            first_file, file_control, is_explore, suffix)
    elif count_splited:
        #FALTA AFINAR FUNCIÓN PARA ESTO
        children_files = File.objects.filter(origin_file=file)
        for ch_file in children_files:
            data = transform_files_in_data(
                ch_file, file_control, is_explore, suffix)
    else:
        data = transform_files_in_data(file, file_control, is_explore, suffix)


def transform_files_in_data(file, file_control, is_explore, suffix)
    data_rows = []
    headers = []
    errors = []
    status_error = 'initial_explore' if is_explore else 'fail_extraction'
    if suffix in ['txt', 'csv']:
        data_rows, errors = get_data_from_file_simple(file)
        if errors:
            file.save_errors(errors, status_error)
            return Response(
                {"errors": errors}, status=status.HTTP_400_BAD_REQUEST)            
        if file.row_headers == 1:
            headers = data_rows.pop(0)
        #file_control.separator = get_separator(data_rows[:40])
        elif file.row_headers:
            errors = ["No podemos procesar ahora headers en posiciones distintas"]
            file.save_errors(errors, status_error)
            return Response(
                {"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        pops_count = file.row_start_data - file.row_headers - 1
        for pop in range(pops_count):
            data_rows.pop(0)
    elif suffix in ['xlsx', 'xls']:
        headers, data_rows, errors = get_data_from_excel(file)
    if errors:
        file.save_errors(errors, status_error)
        return Response(
            {"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
    structured_data = []
    #RICK: Pendiente este tema
    #meta_columns = 
    if is_explore:
        for idx, row in enumerate(data_rows[:50]):
            data_divided = divide_recipe_report_data(row, file, idx)
            if data_divided:
                structured_data.append(data_divided)
        final_response = {"headers": headers, "structured_data": structured_data}
        return Response(final_response, status=status.HTTP_200_OK)
    build_catalogs(file)
    total_rows = len(data_rows)
    inserted_rows = 0
    completed_rows = 0
    for idx, row in enumerate(data_rows):
        data_divided = divide_recipe_report_data(row, file, idx)
        structured_data.append(data_divided)
    for row in structured_data:
        final_row = execute_matches(row, file)


def build_catalogs(file):
    global columns
    global institution
    global state
    institution = file.petition.entity.institution
    state = file.petition.entity.state
    all_columns = NameColumn.objects.filter(file_control=file.file_control)
    columns["all"] = all_columns.values()
    columns["clues"] = all_columns.filter(
        final_field__collection='CLUES').values()
    columns["state"] = all_columns.filter(
        final_field__collection='CLUES').values()
    build_catalog_delegation()
    #RICK, evaluar la segunda condición:
    if not state and columns["state"]:
        build_catalog_state()
    build_catalog_clues()
    for collection, collection_name in collections.items():
        columns[collection] = all_columns.filter(
            final_field__collection=collection_name).values_list('name')


def build_catalog_delegation():
    from catalog.models import Delegation
    global catalog_delegation
    #RICK Evaluar si es necesario declarar global acá:
    global state
    global institution
    curr_delegations = Delegation.objects.filter(institution=institution)
    if state:
        curr_delegations = curr_delegations.filter(state=state)
    delegs_query = list(curr_delegations.values_list(
        'name', 'other_names', 'state__short_name'))
    for deleg in delegs_query:
        try:
            deleg_name = unidecode.unidecode(deleg[0]).upper()
        except Exception:
            deleg_name = deleg[0].upper()
        if deleg_name not in catalog_delegation:
            catalog_delegation[deleg_name] = [deleg]
        alt_names = deleg[1] or []
        for alt_name in alt_names:
            if alt_name not in catalog_delegation:
                catalog_delegation[alt_name] = [deleg]
            else:
                catalog_delegation[alt_name].append(deleg)


def build_catalog_state():
    from catalog.models import State
    global catalog_state
    curr_states = State.objects.all()
    states_query = list(curr_states.values_list('name', 'short_name'))
    for estado in states_query:
        try:
            state_name = unidecode.unidecode(estado[0]).upper()
        except Exception:
            state_name = estado[0].upper()
        if state_name not in catalog_state:
            catalog_state[state_name] = [estado]
        try:
            state_short_name = unidecode.unidecode(estado[1]).upper()
        except Exception:
            state_short_name = estado[1].upper()
        if state_short_name not in catalog_state:
            catalog_state[state_short_name] = [estado]


#Función que se modificará con el trabajo de Itza:
def build_catalog_clues():
    from catalog.models import CLUES
    global catalog_clues
    #RICK Evaluar si es necesario declarar global acá:
    global institution
    global state
    clues_data_query = CLUES.objects.filter(institution=institution)
    if state:
        clues_data_query.filter(state=state)
    clues_data_query = list(
        clues_data_query.values_list(
            "state__name", "name", "tipology_cve",
            "id", "alternative_names", "state__short_name"
        )
    )
    for clues_data in clues_data_query:
        cves = clues_data[2].split("/")
        state_short_name = clues_data[5]
        for cve in cves:
            try:
                clues_name = unidecode.unidecode(clues_data[1])
            except Exception:
                clues_name = clues_data[1]
            prov_name = u"%s %s" % (cve, clues_name)
            real_name = unidecode.unidecode(prov_name).upper()
            if not state:
                real_name = "%s$%s" % (real_name, state_short_name)
            if real_name not in catalog_clues:
                catalog_clues[real_name] = [clues_data]
            else:
                catalog_clues[real_name].append(clues_data)
        if clues_data[4]:
            for alt_name in clues_data[4]:
                if not state:
                    alt_name = "%s$%s" % (alt_name, state_short_name)
                if alt_name not in catalog_clues:
                    catalog_clues[alt_name] = [clues_data]
                else:
                    catalog_clues[alt_name].append(clues_data)


def execute_matches(row, file):    
    from inai import NameColumn, MissingField
    #from formula.models import MissingRow
    delegation = None
    missing_row = None
    if not state:
        columns_state = columns.filter(final_field__collection='State')
        if columns_state.exists():
            state = state_match(row, columns_state, 'State')
    #Delegación
    columns_deleg = columns.filter(final_field__collection='Delegation')
    if columns_deleg.exists():
        delegation = delegation_match(row, columns_state, 'Delegation')
        if not delegation:
            #missing_row = MissingRow.objects.get_or_create(file=file)
            missing_row = MissingRow.objects.create()
        if delegation and not state:
            state = delegation.state
    if not state:


    recipe_row = []


def state_match(row, columns, collection):
    #ITZA: Hay que investigar cómo importar genérico con variable 'collection'
    from catalog.models import State
    query_filter = build_query_filter(row, columns)
    #ITZA: Investigar nombramiento genérico
    state = State.objects.filter(**query_filter).first()
    return state


def delegation_match(row, columns, collection):
    from catalog.models import Delegation
    query_filter = build_query_filter(row, columns)
    delegation = Delegation.objects.filter(**query_filter).first()
    return delegation


def build_query_filter(row, columns):
    query_filter = {}
    for column in columns:
        name_column = column.final_field
        query_filter[name_column] = row[column.position_in_data]
    return query_filter


def split_and_decompress(file):
    import pathlib
    from inai.models import File
    import os
    import zipfile 
    count_splited = 0
    file_name = file.file_name
    suffixes = pathlib.Path(file_name).suffixes
    format_file = file.file_control.format_file
    if 'gz' in suffixes:
        final_path = decompress_file_gz(file_name)
        if final_path != True:
            errors = ['No se pudo descomprimir el archivo gz %s' % final_path]            
            return None, None, errors, None
        file_without_extension = file_path[:-3]
        decompressed_status, created = StatusControl.objects.get_or_create(
            name='decompressed')
        initial_status, created = StatusControl.objects.get_or_create(
            name='initial')
        file.status_process = decompressed_status
        file.save()
        new_file = File.objects.create()
        file = new_file
        suffixes.remove('gz')
    if 'zip' in suffixes:
        [directory, only_name] = file.file_name.rsplit("/", 1)
        [base_name, extension] = only_name.rsplit(".", 1)
        #path_imss_zip = "C:\\Users\\Ricardo\\recetas grandes\\Recetas IMSS\\Septiembre-20220712T233123Z-001.zip"
        zip_file = zipfile.ZipFile(file.file_name)
        all_files = zip_file.namelist()
        with zipfile.ZipFile(file.file_name, 'r') as zip_ref:
            zip_ref.extractall(directory)
        #for f in os.listdir(directory):
        for f in all_files:
            new_file = File.objects.create()
        file = new_file
        suffixes.remove('zip')
    #Obtener el tamaño
    file_name = file.file_name
    if (len(suffixes) != 1):
        errors = [("Tiene más o menos extensiones de las que"
            " podemos reconocer: %s" suffixes)]
        return None, None, errors, None
    if not set(['txt', 'csv', 'xls', 'xlsx']).issubset(suffixes):
        errors = ["Formato no válido", u"%s" % suffixes]
        return None, None, errors, None
    file_size = os.path.getsize(file.file_name)
    if file_size > 400000000:
        if 'xlsx' in suffixes or 'xls' in suffixes:
            errors = ["Archivo excel muy grande, aún no se puede partir"]
            return None, None, errors, None
        file, count_splited = split_file(file)
    return file, count_splited, [], suffixes[0]


#def split_file(path="G:/My Drive/YEEKO/Clientes/OCAMIS/imss"):
def split_file(file):
    from filesplit.split import Split
    from inai.models import File
    [directory, only_name] = file.file_name.rsplit("/", 1)
    [base_name, extension] = only_name.rsplit(".", 1)
    curr_split = Split(file.file_name, directory)
    curr_split.bylinecount(linecount=1000000)
    initial_status = StatusControl.objects.get_or_create(
        name='initial')
    count_splited = 0
    original_file = file.origin_file or file
    for file_num in range(99):
        rr_file_name = "%s_%s.%s" % (base_name, file_num + 1, extension)
        if not os.path.exists(rr_file_name):
            print("Invalid path", rr_file_name)
            break
        if not os.path.isfile(reporte_recetas_path):
            print("Invalid path")
            break
        new_file = File.objects.create()
        count_splited += 1
    if count_splited > 0:
        if file.origin_file:
            file.delete()
        first_file_name = "%s_%s.%s" % (base_name, 1, extension)
        first_file = File.objects.get(file=first_file_name)
        return first_file, count_splited
    else:
        return file, 0

def decompress_file_gz(file_path):
    import gzip
    import shutil
    try:
        with gzip.open(file_path, 'rb') as f_in:
            with open(decomp_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
                return True
    except Exception as e:
        return e


#Divide toda una fila en columnas
def divide_recipe_report_data(row, file=None, row_seq=None):
    from inai.models import NameColumn, MissingRow
    separator = file.file_control.separator
    row_data = row.split(separator) if separator else row
    #Comprobación del número de columnas
    current_columns = NameColumn.objects.filter(file_control=file.file_control)
    columns_count = current_columns.filter(
        position_in_data__isnull=False).count()
    row_seq = row_seq + file.row_start_data
    if len(row_data) == columns_count:
        return [row_seq] + row_data
    else:
        MissingRow.objects.create()
        print("conteo extraño: %s columnas" % rr_data_count)
        print(row_data)
    return None


def get_data_from_file_simple(file):
    from scripts.recipe_specials import (
        special_coma, special_excel, clean_special)
    import io
    try:
        with io.open(file.file_name, "r", encoding="latin-1") as file_open:
            data = file_open.read()
            file_open.close()
    except Exception as e:
        print(e)
        return False, [u"%s" % e]
    is_issste = file.petition.entity.institution.code == 'ISSSTE'
    file_control = file.file_control
    if "|" in data[:5000]:
        file_control.separator = '|'
    elif "," in data[:5000]:
        file_control.separator = ','
        if is_issste:
            data = special_coma(data)
            if ",,," in data[:5000]:
                data = special_excel(data)
    #elif not set([',', '|']).issubset(data[:5000]):
    else:
        return False, ['El documento está vacío']
    file_control.save()
    if is_issste:
        data = clean_special(data)
    rr_data_rows = data.split("\n")
    return rr_data_rows, []


def get_data_from_excel():
    return [], []

