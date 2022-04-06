
def import_reports():
    import csv
    from desabasto.models import (State, Institution, Report, Supply)
    from django.utils.dateparse import parse_datetime
    with open('reportes.csv') as csv_file:
        #contents = f.read().decode("UTF-8")
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            row = [item.decode('latin-1').encode("utf-8") for item in row]
            if not len(row) == 17:
                print("linea: %s" % line_count)
                print(len(row))
                print()
                continue
            if line_count in [0, 1]:
                line_count += 1
            else:
                line_count += 1
                state_inegi_code = row[5]
                try:
                    state = State.objects.get(inegi_code=state_inegi_code)
                except:
                    state = None
                institution_clave = row[7]
                institution = Institution.objects.get(code=institution_clave)
                date_items = row[0].split("/")
                created = parse_datetime(
                    '20%s-%s-%sT12:00:00' % (
                        date_items[2], date_items[1], date_items[0]))
                medicine_type = row[2]
                medicine_name_raw = row[3]
                medicine_real_name = row[4]
                validated = row[16]
                if validated in ["True", "true", True]:
                    validated = True
                else:
                    validated = False
                is_other = row[8]
                if is_other in ["True", "true", True]:
                    is_other = True
                else:
                    is_other = False
                has_corruption = row[10]
                if has_corruption in ["", None]:
                    has_corruption = None
                elif has_corruption in ["True", "true", True]:
                    has_corruption = True
                else:
                    has_corruption = False
                report = Report.objects.create(
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
                Supply.objects.create(
                    medicine_type=medicine_type,
                    medicine_name_raw=medicine_name_raw,
                    medicine_real_name=medicine_real_name,
                    report=report,
                )
                print(report)


def import_clues():
    import csv
    from desabasto.models import (State, Institution, CLUES)
    with open('clues.csv') as csv_file:
        #contents = f.read().decode("UTF-8")
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            row = [item.decode('latin-1').encode("utf-8") for item in row]
            if not len(row) == 25:
                print("linea: %s" % line_count)
                print(len(row))
                print()
                continue
            if line_count in [0, 1]:
                line_count += 1
                continue
            else:
                line_count += 1
                state_inegi_code = row[1]
                try:
                    state = State.objects.get(inegi_code=state_inegi_code)
                except:
                    state = None
                institution_clave = row[2]
                institution = Institution.objects.get(code=institution_clave)
                clues = CLUES.objects.create(
                    name=row[0],
                    state=state,
                    institution=institution,
                    municipality=row[3],
                    municipality_inegi_code=row[4],
                    tipology=row[5],
                    tipology_cve=row[6],
                    id_clues=row[7],
                    clues=row[8],
                    status_operation=row[9],
                    longitude=row[10],
                    latitude=row[11],
                    locality=row[12],
                    locality_inegi_code=row[13],
                    jurisdiction=row[14],
                    jurisdiction_clave=row[15],
                    establishment_type=row[16],
                    consultings_general=int(row[17]) if row[17].isdigit() else 0,
                    consultings_other=int(row[18]) if row[18].isdigit() else 0,
                    beds_hopital=int(row[19]) if row[19].isdigit() else 0,
                    beds_other=int(row[20]) if row[20].isdigit() else 0,
                    total_unities=int(row[21]) if row[21].isdigit() else 0,
                    admin_institution=row[22],
                    atention_level=row[23],
                    stratum=row[24],
                )
                print(clues)


def create_report_supply():
    from desabasto.models import (Report, Supply)
    for report in Report.objects.filter(medicine_type__isnull=False,
                                        medication_name__isnull=False):
        Supply.objects.create(
            medicine_type=report.medicine_type,
            medicine_name_raw=report.medication_name,
            report=report
        )
        report.medicine_type = None
        report.medication_name = None
        report.save()


def update_report_institution():
    from desabasto.models import (Institution, Report)
    for report in Report.objects.filter(institution_raw__isnull=False,
                                        institution__isnull=True):
        try:
            institution = Institution.objects.get(code=report.institution_raw)
            report.institution = institution
            report.save()
        except Exception as e:
            print(e)
            print(report.institution_raw)
            print(report.id)
            print()


def check_report_supply_empty():
    from desabasto.models import (Report, Supply)
    for report in Report.objects.all():
        if not Supply.objects.filter(report=report).exists():
            print(report)
            print(report.id)
            print()


def update_origin_app(old="Yeeko", new="CD2"):
    from desabasto.models import Report
    Report.objects.filter(origin_app=old).update(origin_app=new)


def update_institution_public():
    from desabasto.models import Institution
    for institution in Institution.objects.all():
        institution.public_name = institution.name
        institution.public_code = institution.code
        institution.save()


def set_searcheable_clues():
    from desabasto.models import (CLUES)
    from django.db.models import Q
    is_seach = CLUES.objects.filter(status_operation='EN OPERACION')\
        .exclude(
            Q(institution__code='SMP') | Q(institution__code='HUN') |
            Q(institution__code='CIJ') | Q(institution__code='CRO') |
            Q(establishment_type='DE APOYO') |
            Q(establishment_type='DE ASISTENCIA SOCIAL') |
            Q(tipology_cve='BS') | Q(tipology_cve='X') |
            Q(tipology_cve='P') | Q(tipology_cve='UMM'))
    is_seach.update(is_searchable=True)
