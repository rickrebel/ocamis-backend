# -*- coding: utf-8 -*-
from rest_framework.response import Response
from rest_framework import permissions, views, status
import unidecode
from data_param.models import FinalField
from category.models import StatusControl

recipe_fields = FinalField.objects.filter(
    collection__model_name='Prescription').values()
drug_fields = FinalField.objects.filter(
    collection__model_name='Drug').values()
catalog_clues = {}
catalog_state = {}
catalog_delegation = {}
claves_medico_dicc = {}
columns = {}
institution = None
state = None


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
        return False, ["%s" % e]
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

