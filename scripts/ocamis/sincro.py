# -*- coding: utf-8 -*-


def clean_field(text):
    import re
    try:
        final_txt = text
        final_txt = re.sub(r'(\S|^)\s{2,4}(\S|$)', r'\1 \2', final_txt)
        #espacio antes del cierre de comillas (con cosas intermedias)
        final_txt = re.sub(
            r'(\S)\s\"([^\:|\}|\,]*[\:|\}|\,])', r'\1"\2', final_txt)
        #espacio antes del cierre de comillas
        final_txt = re.sub(r'(\S)\s\"(\:|\}|\,)', r'\1"\2', final_txt)
        #dobles comillas con espacio
        final_txt = re.sub(r'\"\s\"', r'""', final_txt)
        final_txt = final_txt.replace('\\r\\n', '\r\n')
        final_txt = final_txt.replace('\\n', '\n')
        final_txt = final_txt.replace('True', 'true')
        #print final_txt
        return final_txt
    except Exception as e:
        print(e)
        print(text)
        return text



def hydrateCol(row, all_headers):
    hydrated = {}
    cols = row.split("|")
    if not len(cols):
        return False
    for idx_head, header in enumerate(all_headers):
        try:
            if "$" in header:
                header = header.replace("$", "")
                hydrated[header] = clean_field(cols[idx_head])
            else:
                hydrated[header] = cols[idx_head]
        except Exception as e:
            print(e)
            print(cols)
            print(hydrated)
            return False
    return hydrated


def getFileCsv(file_path):
    import io
    with io.open(file_path, "r", encoding="latin-1") as file:
        data = file.read()
        rr_data_rows = data.split("\n")
        headers = rr_data_rows.pop(0)
        all_headers = headers.split("|")
        #print(all_headers)
        return all_headers, rr_data_rows


def generate_file(app_name, model_name):
    from django.apps import apps
    import csv
    MyModel = apps.get_model(app_name, model_name)
    all_objects = MyModel.objects.all().values_list()
    fields = []
    for field in MyModel._meta.fields:
        is_foreign = field.get_internal_type() == 'ForeignKey'
        is_json = field.get_internal_type() == 'JSONField'
        if is_foreign:
            final_name = "%s_id" % field.name
        elif is_json:
            final_name = "%s$" % field.name
        else:
            final_name = field.name
        fields.append(final_name)
    #final_value = clean_field(field.name)
    #fields = [field.name for field in MyModel._meta.fields]
    final_data = list(all_objects)
    final_data.insert(0, fields)
    print(fields)
    csv_path = 'fixture/sincronize/%s.csv' % model_name
    with open(csv_path, 'w', encoding="latin-1", newline="") as csv_file:
        write = csv.writer(csv_file, delimiter='|')
        write.writerows(final_data)
        csv_file.close()

#generate_file('catalog', 'Entity')
#generate_file('catalog', 'State')
#sincronize_entities('catalog', 'State')



def sincronize_entities(app_name, model_name):
    from django.apps import apps
    csv_path = 'fixture/sincronize/%s.csv' % model_name
    all_headers, rr_data_rows = getFileCsv(csv_path)
    #print(all_headers)
    #print(rr_data_rows)
    MyModel = apps.get_model(app_name, model_name)
    for idx, row in enumerate(rr_data_rows):
        if not row:
            break
        hydrated = hydrateCol(row, all_headers)
        print(hydrated)
        elem = MyModel.objects.filter(id=hydrated["id"])
        if elem.exists():
            try:
                del hydrated["id"]
                elem.update(**hydrated)
            except Exception as e:
                print(e)
                elem = None
        else:
            try:
                elem = MyModel.objects.create(**hydrated)
            except Exception as e:
                print(e)

#from scripts.ocamis.sincro import *

#generate_file('category', 'TransparencyLevel')
#sincronize_entities('category', 'TransparencyLevel')

#generate_file('catalog', 'Entity')
#sincronize_entities('catalog', 'Entity')

#generate_file('category', 'DateBreak')
#sincronize_entities('category', 'DateBreak')

#generate_file('category', 'FileType')
#sincronize_entities('category', 'FileType')
