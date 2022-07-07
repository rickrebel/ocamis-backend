# encoding:utf-8


def similar(a, b):
    from difflib import SequenceMatcher
    if a and b:
        return SequenceMatcher(None, a, b).ratio()
    else:
        return 0

# esta función evalúa si hay algún parámetro en el url para el
# redireccionamiento, si no lo hay evalúa si la página de origen es distinta
# a alguna de login o register, para redirigirla al home si es el caso


def get_or_none(model, *args, **kwargs):
    try:
        return model.objects.get(*args, **kwargs)
    except model.DoesNotExist:
        return None


def read_data_dict_CSV(filename, delimiter=',', quotechar='"'):
    import csv
    dictReader = csv.DictReader(open(filename, 'rb'),
                                delimiter=delimiter, quotechar=quotechar)

    datos = []

    for row in dictReader:
        datos.append(row)

    return datos


def get_datetime_mx(datetime_utc):
    import pytz
    cdmx_tz = pytz.timezone("America/Mexico_City")
    return datetime_utc.astimezone(cdmx_tz)

"""

python ./manage.py dumpdata --exclude auth --exclude contenttypes --exclude authtoken --exclude admin.LogEntry --exclude sessions --indent 2 -v 2  > fixture/todo_desabasto.json 

"""