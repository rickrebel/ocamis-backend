# -*- coding: utf-8 -*-

def hydrateCol(row, all_headers):
    hydrated = {}
    cols = row.split("|")
    if not len(cols):
        return False
    for idx_head, header in enumerate(all_headers):
        try:
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
        final_name = "%s_id" % field.name if is_foreign else field.name
        fields.append(final_name)
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


#generate_file('catalog', 'Entity')

#generate_file('category', 'StatusControl')
#sincronize_entities('category', 'StatusControl')

