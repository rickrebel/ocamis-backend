import json
from django.conf import settings


def hydrateCol(row, all_headers):
    hydrated = {}
    cols = row
    if not len(cols):
        return False
    for idx_head, header in enumerate(all_headers):
        try:
            if "$" in header:
                header = header.replace("$", "")
                #hydrated[header] = clean_field(cols[idx_head])
                hydrated[header] = cols[idx_head]
            else:
                hydrated[header] = cols[idx_head]
        except Exception as e:
            print(e)
            print(cols)
            print(hydrated)
            return False
    return hydrated


def getFileJson(file_path):
    #import io
    with open(file_path, "r") as file:
        rr_data_rows = json.load(file)
        headers = rr_data_rows.pop(0)
        return headers, rr_data_rows


def generate_file(app_name, model_name):
    from django.apps import apps
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
    final_data = list(all_objects)
    final_data.insert(0, fields)
    base_dir = settings.BASE_DIR
    json_path = f"{base_dir}\\fixture\\sincronize\\{model_name}.json"
    # json_path = 'fixture/sincronize/%s.json' % model_name
    print("json_path: %s" % json_path)
    print("final_data: %s" % final_data)
    with open(json_path, 'w') as json_file:
        json.dump(final_data, json_file)
        json_file.close()

#generate_file('catalog', 'Entity')
#generate_file('catalog', 'State')
#sincronize_entities('catalog', 'State')

def sincronize_entities(app_name, model_name, field_id="id"):
    from django.apps import apps
    json_path = 'fixture/sincronize/%s.json' % model_name
    all_headers, rr_data_rows = getFileJson(json_path)
    #print(all_headers)
    #print(rr_data_rows)
    MyModel = apps.get_model(app_name, model_name)
    for idx, row in enumerate(rr_data_rows):
        if not row:
            break
        hydrated = hydrateCol(row, all_headers)
        params_query = {field_id: hydrated[field_id]}
        elem = MyModel.objects.filter(**params_query)
        if elem.exists():
            try:
                del hydrated[field_id]
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
#generate_file('category', 'StatusTask')
sincronize_entities('task', 'StatusTask', field_id='name')

#generate_file('catalog', 'Entity')
#sincronize_entities('catalog', 'Entity')

#generate_file('category', 'DateBreak')
#sincronize_entities('category', 'DateBreak')

#generate_file('category', 'FileType')
#sincronize_entities('category', 'FileType')
