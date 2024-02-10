from inai.models import EntityMonth, EntityWeek
from geo.models import Entity


class WeeksGenerator:

    def __init__(self, year: int = None, entity: Entity = None):
        from datetime import datetime
        current_year = datetime.now().year
        self.years = [year] if year else range(2017, current_year + 1)
        self.entity = entity
        self.all_months = []

        self.entities = Entity.objects.all()
        self.entity_months = EntityMonth.objects.all()
        self.entity_weeks = EntityWeek.objects.all()
        if entity:
            self.entities = self.entities.filter(id=entity.id)
            self.entity_weeks = self.entity_weeks.filter(entity=entity)
        if year:
            self.entity_months = self.entity_months.filter(year=year)
            self.entity_weeks = self.entity_weeks.filter(year=year)
        self.already_months = {}
        self.generic_weeks = []

    def get_all_months(self):
        if not self.all_months:
            for year in self.years:
                for month in range(1, 13):
                    current_month = {
                        "year": year,
                        "month": month,
                        "year_month": f"{year}-{month:02d}"
                    }
                    self.all_months.append(current_month)
        return self.all_months

    def get_all_weeks(self, entity: Entity = None) -> list:
        if not entity:
            return self.generic_weeks
        if not entity.split_by_delegation:
            return self.generic_weeks
        all_delegation_ids = list(entity.delegations.values_list(
            'id', flat=True))
        if not all_delegation_ids:
            return self.generic_weeks
        all_weeks = []
        for week in self.generic_weeks:
            for delegation_id in all_delegation_ids:
                current_week = week.copy()
                current_week.update({"iso_delegation_id": delegation_id})
                all_weeks.append(current_week)
        return all_weeks

    def build_generic_weeks(self):
        from datetime import date
        if self.generic_weeks:
            return
        all_months = self.get_all_months()
        for month_data in all_months:
            year = month_data["year"]
            month = month_data["month"]
            every_week = set()
            for day in range(1, 32):
                try:
                    current_date = date(year, month, day)
                except ValueError:
                    break
                iso_year, iso_week, _ = current_date.isocalendar()
                year_week = f"{iso_year}-{iso_week:02d}"
                if year_week in every_week:
                    continue
                every_week.add(year_week)
                current_week = {
                    "iso_week": iso_week,
                    "iso_year": iso_year,
                    "year_week": year_week,
                    "year": year,
                    "month": month,
                    "year_month": month_data["year_month"],
                    "iso_delegation": None
                }
                self.generic_weeks.append(current_week)

    def generate_months(self):
        already_months = self.entity_months.values_list('entity', 'year_month')
        bulk_months = []
        for entity in self.entities:
            all_months = self.get_all_months()
            for month_data in all_months:
                if (entity.id, month_data["year_month"]) in already_months:
                    continue
                month_data.update({"entity": entity})
                bulk_months.append(EntityMonth(**month_data))
        EntityMonth.objects.bulk_create(bulk_months)
        self.entity_months = EntityMonth.objects.all()

    def build_already_months(self):
        entity_months = self.entity_months.values('id', 'entity', 'year_month')
        for month in entity_months:
            entity = month["entity"]
            self.already_months.setdefault(entity, {})
            self.already_months[entity][month["year_month"]] = month["id"]

    def generate_weeks(self):
        already_weeks = self.entity_weeks.values_list(
            'year_week', 'entity', 'year_month', 'iso_delegation')

        self.build_already_months()
        self.build_generic_weeks()
        bulk_weeks = []
        for entity in self.entities:
            final_weeks = self.get_all_weeks(entity)
            for week_data in final_weeks:
                current_week = (
                    week_data["year_week"], entity.id,
                    week_data["year_month"], week_data["iso_delegation"])
                if current_week in already_weeks:
                    continue
                entity_month_id = self.already_months[entity.id][week_data["year_month"]]
                week_data.update({"entity_id": entity.id, "entity_month_id": entity_month_id})
                bulk_weeks.append(EntityWeek(**week_data))
        EntityWeek.objects.bulk_create(bulk_weeks)
        self.entity_weeks = EntityWeek.objects.all()


def create_year():
    # from scripts.ocamis_verified.initial_fields import WeeksGenerator
    weeks_gen = WeeksGenerator(year=2024)
    weeks_gen.generate_months()
    weeks_gen.generate_weeks()


def insert_populations():
    from geo.models import Agency
    pob_states2 = [
        ["01", 955242],
        ["02", 1195226],
        ["03", 565657],
        ["04", 603397],
        ["05", 611034],
        ["06", 492843],
        ["07", 4787898],
        ["08", 2147782],
        ["09", 6521002],
        ["10", 962129],
        ["11", 5237717],
        ["12", 5603620],
        ["13", 3283571],
        ["14", 2906439],
        ["15", 15647621],
        ["16", 2560437],
        ["17", 1149061],
        ["18", 626737],
        ["19", 2158032],
        ["20", 2646110],
        ["21", 5519115],
        ["22", 1784741],
        ["23", 1212873],
        ["24", 2079788],
        ["25", 1804068],
        ["26", 1283074],
        ["27", 1718981],
        ["28", 2623878],
        ["29", 1414381],
        ["30", 4993018],
        ["31", 1824086],
        ["32", 1455943]]
    for pob_st in pob_states2:
        agencies = Agency.objects.filter(
            state__inegi_code=pob_st[0], clues__isnull=True)
        agencies.update(population=pob_st[1])


ISSSTE_DELEGATIONS = [
    ["AGUASCALIENTES", []],
    ["BAJA CALIFORNIA", []],
    ["BAJA CALIFORNIA SUR", []],
    ["CAMPECHE", []],
    ["COAHUILA", []],
    ["COLIMA", []],
    ["CHIAPAS", []],
    ["CHIHUAHUA", []],
    ["DURANGO", []],
    ["GUANAJUATO", []],
    ["GUERRERO", []],
    ["HIDALGO", []],
    ["JALISCO", []],
    ["ESTADO DE MÉXICO", ["MÉXICO"]],
    ["MICHOACÁN", []],
    ["MORELOS", []],
    ["NAYARIT", []],
    ["NUEVO LEÓN", []],
    ["OAXACA", []],
    ["PUEBLA", []],
    ["QUERÉTARO", []],
    ["QUINTANA ROO", []],
    ["SAN LUIS POTOSÍ", ["SAN LUIS POTOSI"]],
    ["SINALOA", []],
    ["SONORA", []],
    ["TABASCO", []],
    ["TAMAULIPAS", []],
    ["TLAXCALA", []],
    ["VERACRUZ", []],
    ["YUCATÁN", []],
    ["ZACATECAS", []],
    ["CD.MX. ZONA NORTE", ["ZONA NORTE"]],
    ["CD.MX. ZONA ORIENTE", ["ZONA ORIENTE"]],
    ["CD.MX. ZONA PONIENTE", ["ZONA PONIENTE"]],
    ["CD.MX. ZONA SUR", ["ZONA SUR"]],
]


def import_delegations():
    from geo.models import Delegation, State, Institution
    issste = Institution.objects.get(code="ISSSTE")
    Delegation.objects.filter(institution=issste).delete()
    for delegation in ISSSTE_DELEGATIONS:
        try:
            if "CD.MX." in delegation[0] or "ZONA " in delegation[0]:
                state = State.objects.get(code_name="CDMX")
            else:
                state = State.objects.get(short_name__icontains=delegation[0])
        except State.DoesNotExist:
            print("State not found: ", delegation)
            continue
        except State.MultipleObjectsReturned:
            print("Multiple states found: ", delegation)
            state = State.objects.get(short_name__iexact=delegation[0])
        #Delegation.objects.get_or_create(
        Delegation.objects.create(
            name=delegation[0], state=state, institution=issste,
            other_names=delegation[1])

# import_delegations()


def generate_insabi_delegations():
    from geo.models import Delegation, State, Institution
    insabi = Institution.objects.get(code="INSABI")
    states = State.objects.all()
    for state in states:
        name = f"{state.short_name} - INSABI"
        Delegation.objects.get_or_create(
            name=name, state=state, institution=insabi)


UMAES = [
    ['UMAE Cardiología en Nuevo León', "NLIMS000315"],
    ['UMAE Cardiología C.M.N. Siglo XXI', "DFIMS000575"],
    ['UMAE Especialidades C.M.N. La Raza', "DFIMS000020"],
    ['UMAE Especialidades C.M.N. Siglo XXI', "DFIMS000580"],
    ['UMAE Especialidades Coahuila', "CLIMS000490"],
    ['UMAE Especialidades Guanajuato', "GTIMS000226"],
    ['UMAE Especialidades Jalisco', "JCIMS000301"],
    ['UMAE Especialidades Nuevo León', "NLIMS000303"],
    ['UMAE Especialidades Puebla', "PLIMS000200"],
    ['UMAE Especialidades Sonora', "SRIMS000150"],
    ['UMAE Especialidades Veracruz (Nte.)', "VZIMS001112"],
    ['UMAE Especialidades Yucatán', "YNIMS000071"],
    ['UMAE Gineco - Obstetricia Jalisco', "JCIMS000313"],
    ['UMAE Gineco - Obstetricia La Raza', "DFIMS000044"],
    ['UMAE Gineco - Obstetricia No. 4 (D.F. Sur)', "DFIMS000452"],
    ['UMAE Gineco - Obstetricia Nuevo León', "NLIMS000320"],
    ['UMAE Gineco - Pediatría Guanajuato', "GTIMS000231"],
    ['UMAE Hospital General C.M.N. La Raza', "DFIMS000061"],
    ['UMAE Oncología C.M.N. Siglo XXI', "DFIMS000604"],
    ['UMAE Pediatría C.M.N. Siglo XXI', "DFIMS000616"],
    ['UMAE Pediatría Jalisco', "JCIMS000325"],
    ['UMAE Trauma y Orto M.S. "Dr. Victorio de la Fuente Narváez"', "DFIMS000213"],
    ['UMAE Traumatología y Ortopedia Lomas Verdes', "MCIMS000454"],
    ['UMAE Traumatología y Ortopedia Nuevo León', "NLIMS000344"],
    ['UMAE Traumatología y Ortopedia Puebla', "PLIMS000212"]]

IMSS_DELEGATIONS = [
    ["DELEG NORTE", "Ciudad de México"],
    ["DELEG SUR", "Ciudad de México"],
    ["EDOMEX ORIENTE", "Estado de México"],
    ["EDOMEX PONIENTE", "Estado de México"],
    ["VERACRUZ PUERTO", "VERACRUZ"],
    ["VERACRUZ SUR", "VERACRUZ"]]


def generate_imss_delegations():
    from geo.models import Delegation, State, Institution, CLUES
    imss = Institution.objects.get(code="IMSS")
    states = State.objects.all()
    for state in states:
        short_name = state.short_name.upper()
        if short_name in ["VERACRUZ", "CIUDAD DE MÉXICO", "ESTADO DE MÉXICO"]:
            continue
        deleg, created = Delegation.objects.get_or_create(
            name=short_name, state=state, institution=imss)
    for delegation_name, clues_clave in UMAES:
        clues = CLUES.objects.get(clues=clues_clave)
        delegation, c = Delegation.objects.get_or_create(
            name=delegation_name, institution=imss,
            is_clues=True, state=clues.state)
        # print("Delegation: ", delegation)
        alternative_names = clues.alternative_names or []
        alternative_names.append(delegation_name)
        clues.delegation = delegation
        clues.alternative_names = alternative_names
        clues.save()
    for delegation_name, state_name in IMSS_DELEGATIONS:
        state = State.objects.get(short_name__iexact=state_name)
        Delegation.objects.get_or_create(
            name=delegation_name, institution=imss, state=state)


def get_file_csv(file_path):
    import io
    with io.open(file_path, "r", encoding="utf-8") as file:
        data = file.readlines()
        # rr_data_rows = data.split("\n")
        # headers = rr_data_rows.pop(0)
        # all_headers = headers.split("|")
        # print(all_headers)
        return data


def find_lines_with_regex(file_path="fixture/catalogo_clues_issste.txt"):
    import re
    from geo.models import CLUES
    all_lines = get_file_csv(file_path)
    not_found_clues = []
    for line in all_lines:
        # with regex, extract the string like this: "DFIST000312 096-201-00"
        regex_format = r'\s(\w{5}\d{6})\s(\d{3}\-\d{3}\-\d{2})\s'
        match = re.search(regex_format, line)
        if not match:
            continue
        clues_key = match.group(1)
        key_issste = match.group(2)
        try:
            clues = CLUES.objects.get(clues=clues_key)
            clues.key_issste = key_issste
            clues.save()
        except CLUES.DoesNotExist:
            not_found_clues.append(clues_key)
    return not_found_clues


def find_municipalities_with_regex(file_path="fixture/municipios_inegi_2023.txt"):
    import re
    from geo.models import Municipality, State
    success_count = 0
    regex_matches = 0
    all_lines = get_file_csv(file_path)
    not_found_muni = []
    all_states = State.objects.all()
    states_dict = {state.inegi_code: state.id for state in all_states}
    all_municipalities = Municipality.objects.all()
    municipalities_dict = {}
    for municipality in all_municipalities:
        mun_inegi = municipality.inegi_code
        if len(mun_inegi) != 3:
            mun_inegi = mun_inegi.zfill(3)
            municipality.inegi_code = mun_inegi
            municipality.save()
        key = f"{municipality.state.inegi_code}-{mun_inegi}"
        municipalities_dict[key] = municipality.id
    regex_format = (r'^(\d{2})(\D+)\s(\d{3})\s([a-zA-Z\s]+?)'
                    r'(?= Zona Libre de la Frontera Norte| Resto del País)')
    for line in all_lines:
        match = re.search(regex_format, line)
        if not match:
            continue
        regex_matches += 1
        entity_key = match.group(1)
        municipality_key = match.group(3)
        municipality_name = match.group(4)
        key = f"{entity_key}-{municipality_key}"
        if key not in municipalities_dict:
            try:
                success_count += 1
                # Municipality(
                Municipality.objects.create(
                    inegi_code=municipality_key,
                    name=municipality_name,
                    state_id=states_dict[entity_key])
                municipalities_dict[key] = True
            except Exception as e:
                not_found_muni.append([key, municipality_name, e])
    print("success_count: ", success_count)
    print("regex_matches: ", regex_matches)
    print("not_found_muni: ", len(not_found_muni))
    return not_found_muni


# missing_clues = find_lines_with_regex()
# missing_munis = find_municipalities_with_regex()
