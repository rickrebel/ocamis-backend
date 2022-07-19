# -*- coding: utf-8 -*-
from rest_framework.response import Response
from rest_framework import permissions, views, status

#path_imss = "G:\\Mi unidad\\YEEKO\\Proyectos\\OCAMIS\\imss\\req_abril_2019_02.txt.gz"
#decompress_file_gz(path_imss)
from parameter.models import FinalField
recipe_fields = FinalField.objects.filter(
    collection__model_name='RecipeReport2').values()
medicine_fields = FinalField.objects.filter(
    collection__model_name='RecipeMedicine2').values()


def start_file_process(file, group_file, is_explore=False):
    from files_rows.models import File
    file.error_process = None
    file.save()
    data_rows = []
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
    if is_explore:
        data = transform_files_in_data(first_file, group_file, is_explore)
    elif count_splited:
        #FALTA AFINAR FUNCIÓN PARA ESTO
        children_files = File.objects.filter(origin_file=file)
        for ch_file in children_files:
            data = transform_files_in_data(ch_file, group_file, is_explore)
    else:
        data = transform_files_in_data(file, group_file, is_explore)


def transform_files_in_data(file, group_file, is_explore)
    data_rows = []
    headers = []
    status_error = 'initial_explore' if is_explore else 'fail_extraction'
    if suffix in ['txt', 'csv']:
        data_rows, errors = get_data_from_file_simple(file)
        if errors:
            file.save_errors(errors, status_error)
            return Response(
                {"errors": errors}, status=status.HTTP_400_BAD_REQUEST)            
        if file.row_headers == 1:
            headers = data_rows.pop(0)
        #group_file.separator = get_separator(data_rows[:40])
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
    for idx, row in enumerate(data_rows):
        data_divided = divide_recipe_report_data(row, file, idx)
        structured_data.append(data_divided)
    for row in structured_data:
        final_row = execute_matches(row, file)


def execute_matches(row, file):    
    from files_rows import Column, MissingField, MissingRow
    columns = Column.objects.filter(group_file=file.group_file)
    institution = file.petition.entity.institution
    state = file.petition.entity.state
    delegation = None
    missing_row = None
    if not state:
        columns_state = columns.filter(final_data__collection='State')
        if columns_state.exists():
            state = generic_match(row, columns_state, 'State')
    #Delegación
    columns_deleg = columns.filter(final_data__collection='Delegation')
    if columns_deleg.exists():
        delegation = delegation_match(row, columns_state, 'Delegation')
        if not delegation:
            #missing_row = MissingRow.objects.get_or_create(file=file)
            missing_row = MissingRow.objects.create(
                file=file, row_seq = row[0], orinal_data=row)
        if delegation and not state:
            state = delegation.state
    if not state:


    recipe_row = []


def generic_match(row, columns, collection):
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
    from files_rows.models import File
    from files_categories.models import StatusProcess
    import os
    import zipfile 
    count_splited = 0
    file_name = file.file_name
    suffixes = pathlib.Path(file_name).suffixes
    format_file = file.group_file.format_file
    if 'gz' in suffixes:
        final_path = decompress_file_gz(file_name)
        if final_path != True:
            errors = ['No se pudo descomprimir el archivo gz %s' % final_path]            
            return None, None, errors, None
        file_without_extension = file_path[:-3]
        decompressed_status, created = StatusProcess.objects.get_or_create(
            name='decompressed')
        initial_status, created = StatusProcess.objects.get_or_create(
            name='initial')
        file.status_process = decompressed_status
        file.save()
        new_file = File.objects.create(
            file=file_without_extension,
            origin_file=file,
            date=file.date,
            status=initial_status,
            #Revisar si lo más fácil es poner o no los siguientes:
            group_file=group_file,
            petition=file.petition,
            petition_month=file.petition_month,
            )
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
            new_file = File.objects.create(
                file="%s%s" % (directory, f),
                origin_file=file,
                date=file.date,
                status=initial_status,
                #Revisar si lo más fácil es poner o no los siguientes:
                group_file=group_file,
                petition=file.petition,
                petition_month=file.petition_month,
                )
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
    from files_categories.models import StatusProcess
    from files_rows.models import File
    [directory, only_name] = file.file_name.rsplit("/", 1)
    [base_name, extension] = only_name.rsplit(".", 1)
    curr_split = Split(file.file_name, directory)
    curr_split.bylinecount(linecount=1000000)
    initial_status = StatusProcess.objects.get_or_create(
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
        new_file = File.objects.create(
            file=rr_file_name,
            origin_file=original_file,
            date=original_file.date,
            status=initial_status,
            #Revisar si lo más fácil es poner o no los siguientes:
            group_file=original_file.group_file,
            petition=original_file.petition,
            petition_month=original_file.petition_month)
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
    from files_rows.models import Column, MissingRows
    separator = file.group_file.separator
    row_data = row.split(separator) if separator else row
    #Comprobación del número de columnas
    current_columns = Column.objects.filter(group_file=file.group_file)
    columns_count = current_columns.filter(
        position_in_data__isnull=False).count()
    row_seq = row_seq + file.row_start_data
    if len(row_data) == columns_count:
        return [row_seq] + row_data
    else:
        MissingRows.objects.create(
            file=file,
            original_data=row_data,
            row_seq=row_seq,
        )
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
    group_file = file.group_file
    if "|" in data[:5000]:
        group_file.separator = '|'
    elif "," in data[:5000]:
        group_file.separator = ','
        if is_issste:
            data = special_coma(data)
            if ",,," in data[:5000]:
                data = special_excel(data)
    #elif not set([',', '|']).issubset(data[:5000]):
    else:
        return False, ['El documento está vacío']
    group_file.save()
    if is_issste:
        data = clean_special(data)
    rr_data_rows = data.split("\n")
    return rr_data_rows, []


def get_data_from_excel():
    return [], []

