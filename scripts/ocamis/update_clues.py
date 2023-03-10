import pandas as pd


def clean_na(row):
    cols = row.tolist()
    return [col.strip() if isinstance(col, str) else "" for col in cols]


def convert_municipality_code():
    from catalog.models import Municipality
    all_municipalities = Municipality.objects.all()
    for municipality in all_municipalities:
        initial_code = int(municipality.inegi_code)
        if initial_code < 10:
            inegi_code = f"00{municipality.inegi_code}"
        elif initial_code < 100:
            inegi_code = f"0{municipality.inegi_code}"
        else:
            inegi_code = f"{municipality.inegi_code}"
        municipality.inegi_code = inegi_code
        municipality.save()


equivalences = [
    ["CLUES", "clues"],
    ["CLAVE DEL MUNICIPIO", "municipality_inegi_code"],
    ["NOMBRE DE LA LOCALIDAD", "locality"],
    ["CLAVE DE LA LOCALIDAD", "locality_inegi_code"],
    ["NOMBRE DE LA JURISDICCION", "jurisdiction"],
    ["CLAVE DE LA JURISDICCION", "jurisdiction_clave"],
    ["NOMBRE TIPO ESTABLECIMIENTO", "establishment_type"],
    ["NOMBRE DE TIPOLOGIA", "typology"],
    ["CLAVE DE TIPOLOGIA", "typology_cve"],
    ["NOMBRE DE LA UNIDAD", "name"],
    ["TIPO DE VIALIDAD", "type_street"],
    ["VIALIDAD", "street"],
    ["CODIGO POSTAL", "postal_code"],
    ["ESTATUS DE OPERACION", "status_operation"],
    ["RFC DEL ESTABLECIMIENTO", "rfc"],
    ["LATITUD", "longitude"],
    ["LONGITUD", "latitude"],
    ["NOMBRE DE LA INS ADM", "admin_institution"],
    ["NIVEL ATENCION", "atention_level"],
    ["ESTRATO UNIDAD", "stratum"],
]

integers_equivalences = [
    ["CONSULTORIOS DE MED GRAL", "consultings_general"],
    ["CONSULTORIOS EN OTRAS AREAS", "consultings_other"],
    ["CAMAS EN AREA DE HOS", "beds_hopital"],
    ["CAMAS EN OTRAS AREAS", "beds_other"],
]


def read_excel(data_excel):
    from datetime import datetime
    from django.utils import timezone
    from catalog.models import CLUES, State, Institution, Municipality
    iter_data = data_excel.apply(clean_na, axis=1)
    # rows = data_excel.iterrows()
    list_val = iter_data.tolist()
    headers = list_val[0]
    data = list_val[1:]
    all_states = State.objects.all()
    state_dict = {state.inegi_code: state.id for state in all_states}
    all_municipalities = Municipality.objects.all()
    municipality_dict = {}
    for municipality in all_municipalities:
        # CONVERT TO TRIPLE DIGIT, EXAMPLE: 001
        municipality_dict[f"{municipality.state.inegi_code}-{municipality.inegi_code}"] = municipality.id
    municipality_dict = {f"{municipality.state.inegi_code}-{municipality.inegi_code}":
                            municipality.id for municipality in all_municipalities}
    all_institutions = Institution.objects.all()
    institution_dict = {institution.code: institution.id
                        for institution in all_institutions}
    institution_dict["SSA"] = institution_dict["INSABI"]
    sum_fields = {
        "total_unities": [
            "CONSULTORIOS DE MED GRAL",
            "CONSULTORIOS EN OTRAS AREAS",
            "CAMAS EN AREA DE HOS",
            "CAMAS EN OTRAS AREAS",
        ],
    }
    concat_fields = {
        "sheet_number": ["NUMERO EXTERIOR", "NUMERO INTERIOR"],
        "suburb": ["TIPO DE ASENTAMIENTO", "ASENTAMIENTO"],
    }
    for row in data:
        row_dict = dict(zip(headers, row))
        # year = int(last_change[:4])
        clues_key = row_dict["CLUES"]
        try:
            clues = CLUES.objects.get(clues=clues_key)
        except CLUES.DoesNotExist:
            clues = CLUES()
            clues.id_clues = clues_key
            clave_ent = row_dict["CLAVE DE LA ENTIDAD"]
            clues.state_id = state_dict[clave_ent]
            clave_mun = f"{clave_ent}-{row_dict['CLAVE DEL MUNICIPIO']}"
            try:
                clues.municipality_id = municipality_dict[clave_mun]
            except KeyError:
                print(f"Error saving clues {clues_key}: Municipality {row_dict['CLAVE DEL MUNICIPIO']} not found")
            try:
                clues.institution_id = institution_dict[row_dict["CLAVE DE LA INSTITUCION"]]
            except KeyError:
                print(f"Error saving clues {clues_key}: Institution {row_dict['CLAVE DE LA INSTITUCION']} not found")
        last_change = row_dict["FECHA ULTIMO MOVIMIENTO"]
        if last_change:
            date_change = datetime.strptime(last_change, "%Y-%m-%d")
            date_change = timezone.make_aware(date_change)
            clues.last_change = date_change
        for equivalence in equivalences:
            clues.__dict__[equivalence[1]] = row_dict[equivalence[0]]
        for equivalence in integers_equivalences:
            clues.__dict__[equivalence[1]] = int(row_dict[equivalence[0]])
        for field in sum_fields:
            clues.__dict__[field] = sum(
                [int(row_dict[field]) for field in sum_fields[field]])
        for field in concat_fields:
            clues.__dict__[field] = " ".join(
                [row_dict[field] for field in concat_fields[field]])
        try:
            clues.save()
        except Exception as e:
            print(f"Error saving clues {clues_key}: {e}")
            continue


path = "C:\\Users\\Ricardo\\dev\\desabasto\\desabasto-api\\fixture\\ESTABLECIMIENTO_SALUD_202301.xlsx"

excel_file = pd.ExcelFile(path)
data_excel = excel_file.parse(
    "CLUES_ENERO_2023",
    dtype='string', na_filter=False,
    keep_default_na=False, header=None)


read_excel(data_excel)


def clean_repeated_clues():
    from catalog.models import CLUES
    from django.db.models import Count
    repeated_clues = CLUES.objects.values('clues').annotate(
        count=Count('clues')).filter(count__gt=1)
    for clues in repeated_clues:
        clues = CLUES.objects.filter(clues=clues['clues'])
        clues = clues.order_by('-last_change')
        for clue in clues[1:]:
            clue.delete()

