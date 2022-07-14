
def import_reports():
    import csv
    from desabasto.models import (State, Institution, Report, Supply)
    from django.utils.dateparse import parse_datetime
    with open('reportes.csv') as csv_file:
        #contents = f.read().decode("UTF-8")
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            row=[item.decode('latin-1').encode("utf-8") for item in row]
            if not len(row) == 17:
                print "linea: %s"%line_count
                print len(row)
                print
                continue
            if line_count in [0,1]:
                line_count += 1
            else:
                line_count += 1
                state_inegi_code=row[5]
                try:
                    state=State.objects.get(inegi_code=state_inegi_code)
                except Exception as e:
                    state=None
                institution_clave=row[7]
                institution=Institution.objects.get(code=institution_clave)
                date_items=row[0].split("/")
                created=parse_datetime('20%s-%s-%sT12:00:00'%(date_items[2],
                    date_items[1], date_items[0]))
                medicine_type=row[2]
                medicine_name_raw=row[3]
                medicine_real_name=row[4]
                validated=row[16]
                if validated in ["True", "true", True]:
                    validated=True
                else:
                    validated=False
                is_other=row[8]
                if is_other in ["True", "true", True]:
                    is_other=True
                else:
                    is_other=False
                has_corruption=row[10]
                if has_corruption in ["", None]:
                    has_corruption=None
                elif has_corruption in ["True", "true", True]:
                    has_corruption=True
                else:
                    has_corruption=False
                report=Report.objects.create(
                    informer_type=row[1],
                    state=state,
                    institution_raw=row[6],
                    institution=institution,
                    is_other=is_other,
                    hospital_name_raw=row[9],
                    has_corruption=has_corruption,
                    informer_name=row[11],
                    email=row[12],
                    phone=row[13],
                    origin_app=row[14],
                    disease=row[15],
                    validated=validated
                )
                Report.objects.filter(id=report.id).update(created=created)
                supply=Supply.objects.create(
                    medicine_type=medicine_type,
                    medicine_name_raw=medicine_name_raw,
                    medicine_real_name=medicine_real_name,
                    report=report,
                )
                print report


def create_report_supply():
    from desabasto.models import (State, Institution, Report, Supply)
    for report in Report.objects.filter(
        medicine_type__isnull=False, medication_name__isnull=False):
        supply=Supply.objects.create(
            medicine_type=report.medicine_type,
            medicine_name_raw=report.medication_name,
            report=report
        )
        report.medicine_type=None
        report.medication_name=None
        report.save()

def update_report_institution():
    from desabasto.models import (State, Institution, Report, Supply)
    for report in Report.objects.filter(
        institution_raw__isnull=False, institution__isnull=True):
        try:
            institution=Institution.objects.get(code=report.institution_raw)
            report.institution=institution
            report.save()
        except Exception as e:
            print e
            print report.institution_raw
            print report.id
            print

def check_report_supply_empty():
    from desabasto.models import (State, Institution, Report, Supply)
    for report in Report.objects.all():
        if not Supply.objects.filter(report=report).exists():
            print report
            print report.id
            print

def update_origin_app(old="Yeeko", new="CD2"):
    from desabasto.models import Report
    Report.objects.filter(origin_app=old).update(origin_app=new)
