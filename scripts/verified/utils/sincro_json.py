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
    # import io
    with open(file_path, "r") as file:
        rr_rows = json.load(file)
        headers = rr_rows.pop(0)
        return headers, rr_rows


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
    is_local = settings.IS_LOCAL
    if is_local:
        json_path = f"{base_dir}\\fixture\\sincronize\\{model_name}.json"
    else:
        json_path = f"{base_dir}/fixture/sincronize/{model_name}.json"
    # json_path = 'fixture/sincronize/%s.json' % model_name
    print("json_path: %s" % json_path)
    print("final_data: %s" % final_data)
    with open(json_path, 'w') as json_file:
        json.dump(final_data, json_file)
        json_file.close()


def sincronize_entities(app_name, model_name, field_id="id"):
    from django.apps import apps
    json_path = 'fixture/sincronize/%s.json' % model_name
    all_headers, rr_rows = getFileJson(json_path)
    MyModel = apps.get_model(app_name, model_name)
    for idx, row in enumerate(rr_rows):
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


print("HOLI")

# from scripts.verified.sincro_json import sincronize_entities, generate_file

# generate_file('data_param', 'Collection')
# sincronize_entities('data_param', 'Collection')

# generate_file('data_param', 'FinalField')
# sincronize_entities('data_param', 'FinalField')

# generate_file('category', 'FileType')
# sincronize_entities('inai', 'FileType', field_id='name')
#
# generate_file('classify_task', 'Stage')
# sincronize_entities('classify_task', 'Stage', field_id='name')

# generate_file('task', 'TaskFunction', field_id='name')
# sincronize_entities('task', 'TaskFunction', field_id='name')

# sincronize_entities('category', 'StatusControl')
# sincronize_entities('data_param', 'DataGroup')
