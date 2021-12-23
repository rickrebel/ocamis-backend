from desabasto.models import Supply, Disease, Component, CLUES
import csv
# from scripts.common import read_data_dict_CSV
from django.db.models import Q


def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [str(cell, 'utf-8') for cell in row]


def insert_clean_data(limit=None):
    filename = 'andres_exercise.csv'
    reader = unicode_csv_reader(open(filename))
    count = -1

    last_report = 0
    diseases_not_found = []
    clues_not_found = []
    count = 0
    success = 0
    success_clues = 0
    success_comp = 0
    for supp_id, report_id, dis, clu, comp in reader:
        if count == -1:
            continue
        count += 1
        same_report = last_report == report_id
        if dis or comp or (
                not same_report and clu):
            try:
                supply = Supply.objects.get(id=int(supp_id))
            except Exception as e:
                print(e)
                print(supp_id)
                continue
            if dis:
                disease, created = Disease.objects.get_or_create(
                    name=dis)
                supply.disease = disease
                success += 1
            if comp and not supply.component:
                try:
                    final_comp = comp.strip()
                    component = Component.objects.get(
                        Q(name__icontains=final_comp) |
                        Q(alias__icontains=final_comp)
                    )
                    supply.component = component
                    success_comp += 1
                except Exception as e:
                    print(e)
                    print(supp_id)
                    print(comp)
                    supply.medicine_name_raw = u"!! %s" % comp
                    if comp not in diseases_not_found:
                        diseases_not_found.append(comp)
            if not same_report and clu:
                report = supply.report
                try:
                    clues = CLUES.objects.get(clues=clu)
                    report.clues = clues
                    report.save()
                    success_clues += 1
                except Exception:
                    print(clu)
                    clues_not_found.append(clu)
            supply.save()
        last_report = report_id

    print(success)
    print(success_clues)
    print(success_comp)
    print(len(clues_not_found))
    print(len(diseases_not_found))

    diseases_not_found

    for disease in diseases_not_found:
        print(disease)
