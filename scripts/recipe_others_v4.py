# -*- coding: utf-8 -*-
from rest_framework.response import Response
from rest_framework import permissions, views, status


def explore_first_time(file, group_file):
    import pathlib
    print(pathlib.Path('yourPath.example').suffix) # '.example'
    print(pathlib.Path("hello/foo.bar.tar.gz").suffixes) # ['.bar', '.tar', '.gz']
    #REVISAR:
    suffixes = pathlib.Path(file.file_name).suffixes
    #format_file = group_file.format_file
    if 'txt' in suffixes or 'csv' in suffixes:
        group_file.separator = get_separator()
        get_data_from_file_simple()
    elif 'xlsx' in suffixes or 'xls' in suffixes:
        get_data_from_excel()
    else:
        errors = ["Formato no válido", u"%s" % suffixes]
        file.error_process = errors
        return Response(
            {"errors": errors}, status=status.HTTP_400_BAD_REQUEST)


def get_data_from_file_simple(reporte_recetas_path):
    import io
    try:
        with io.open(reporte_recetas_path, "r", encoding="latin-1") as file:
            data = file.read()
            file.close()
    except Exception as e:
        print(e)
        return False, [u"%s" % (e)], False
    rr_data_rows = data.split("\n")
    return rr_data_rows, []



#Divide toda una fila en columnas
def divide_recipe_report_data(
        text_data, control_parameter=None, file=None, row_seq=None):
    recipe_report_data = text_data.split("|")
    rr_data_count = len(recipe_report_data)
    #Comprobación del número de columnas
    from files_rows.models import Column, MissingRows
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



