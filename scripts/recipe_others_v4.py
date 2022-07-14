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


def get_data_from_excel():
    print("Por ahora no está desarrollado")



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



