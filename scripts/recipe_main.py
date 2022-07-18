# -*- coding: utf-8 -*-
from rest_framework.response import Response
from rest_framework import permissions, views, status

#path_imss = "G:\\Mi unidad\\YEEKO\\Proyectos\\OCAMIS\\imss\\req_abril_2019_02.txt.gz"
#decompress_file_gz(path_imss)

def transform_data(file, group_file, is_explore=False):
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
    if suffix in ['txt', 'csv']:
        group_file.separator = get_separator()
        data_rows, errors = get_data_from_file_simple(file)
    elif suffix in ['xlsx', 'xls']:
        data_rows, errors = get_data_from_excel(file)
    if errors:
        file.save_errors(errors)
        return Response(
            {"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

def get_data_from_excel():
    return [], []


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
        path_imss_zip = "C:\\Users\\Ricardo\\recetas grandes\\Recetas IMSS\\Septiembre-20220712T233123Z-001.zip"
        with zipfile.ZipFile(file.file_name, 'r') as zip_ref:
            zip_ref.extractall(directory)
        for f in os.listdir(directory):
            print(f)
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

            full_file_path = "%s%s" % (mypath, f)
            if isfile(full_file_path) and (".png" in f and "PP-" in f):
                all_pdf_files.append([f, full_file_path])



        suffixes.remove('gz')
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




catalgo_tipologies ['UMF', 'HRM']





#Divide toda una fila en columnas
def divide_recipe_report_data(
        text_data, control_parameter=None, file=None, row_seq=None):
    from files_rows.models import Column, MissingRows
    recipe_report_data = text_data.split("|")
    rr_data_count = len(recipe_report_data)
    #Comprobación del número de columnas
    current_columns = Column.objects.filter(
        group_file__controlparameters=control_parameter)
    columns_count = current_columns.filter(
        position_in_data__isnull=False).count()
    if rr_data_count == columns_count:
    #if rr_data_count == 14:
        return recipe_report_data
    else:
        MissingRows.objects.create(
            file=file,
            original_data=recipe_report_data,
            row_seq=row_seq
        )
        print("conteo extraño: %s columnas" % rr_data_count)
        print(recipe_report_data)
    return None


def get_data_from_file_simple(file):
    import io
    try:
        with io.open(file.file_name, "r", encoding="latin-1") as file_open:
            data = file_open.read()
            file_open.close()
    except Exception as e:
        print(e)
        return False, [u"%s" % e]
    rr_data_rows = data.split("\n")
    return rr_data_rows, []


def get_data_from_file(
        reporte_recetas_path, clean_data=True):
    import io

    with_coma = False
    from_excel = False
    try:
        # with open(reporte_recetas_path) as file:
        #with io.open(reporte_recetas_path, "r", encoding="latin-1") as file:
        with io.open(reporte_recetas_path, "r", encoding="latin-1") as file:
            data = file.read()
            if "|" not in data[:3000]:
                with_coma = True
            if "," not in data[:5000] and "|" not in data[:5000]:
                print("-------------------")
                print('empty %s' % reporte_recetas_path)
                return False, ['empty %s' % reporte_recetas_path], False
            if ",,," in data[:5000]:
                from_excel = True

            if clean_data:
                if with_coma:
                    data = special_coma(data)
                if from_excel:
                    data = special_excel(data)
                data = data.replace("\"", "").replace(first_null, "")
                data = clean_special(data)
            file.close()
    except Exception as e:
        return False, [u"%s" % (e)], False

    rr_data_rows = data.split(sep_rows)
    if not with_coma:
        headers = rr_data_rows.pop(0)
        print(u"se quitó headers del procesado: ", headers)

    return rr_data_rows, [], with_coma



