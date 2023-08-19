
def generate_months():
    from inai.models import EntityMonth
    from geo.models import Entity
    # for agency in Agency.objects.all():
    for entity in Entity.objects.all():
        for sum_year in range(6):
            year = sum_year + 2017
            for month in range(12):
                month += 1
                ye_mo = f"{year}-{month:02d}"
                EntityMonth.objects.get_or_create(
                    entity=entity,
                    year_month=ye_mo,
                    year=year,
                    month=month)
                # print("%s-%s" % (agency.id, ye_mo))


def generate_weeks():
    from inai.models import EntityMonth, EntityWeek
    from geo.models import Entity
    from datetime import timedelta, date
    # for agency in Agency.objects.all():
    for entity in Entity.objects.all():
        if entity.split_by_delegation:
            all_delegation_ids = entity.delegations.values_list(
                'id', flat=True)
        else:
            all_delegation_ids = [None]
            # continue
        new_weeks = []
        already_weeks = EntityWeek.objects.filter(entity=entity)\
            .values('year_week', 'entity', 'year_month', 'iso_delegation')
        # space
        def add_new_weeks(
                init_week, last_week, year_int, ent_month, iso_delegation):
            ye_mo = ent_month.year_month
            year_by_ym, month_by_ym = ye_mo.split('-')
            for week in range(init_week, last_week + 1):
                year_week = f"{year_int}-{week:02d}"
                if not any(
                        d['year_week'] == year_week
                        and d['entity'] == entity.id
                        and d['year_month'] == ye_mo
                        and d['iso_delegation'] == iso_delegation
                        for d in already_weeks):
                    new_weeks.append(EntityWeek(
                        entity=entity,
                        entity_month=ent_month,
                        year_week=year_week,
                        iso_year=year_int,
                        iso_week=week,
                        year_month=ent_month.year_month,
                        year=int(year_by_ym),
                        month=int(month_by_ym),
                        iso_delegation=iso_delegation))
        for year in range(2017, 2024):
            for month in range(1, 13):
                year_month = f"{year}-{month:02d}"
                entity_month, created = EntityMonth.objects.get_or_create(
                    entity=entity, year_month=year_month)
                # space
                start_date = date(year, month, 1)
                start_week = start_date.isocalendar()[1]
                start_year = start_date.isocalendar()[0]
                # space
                is_december = month == 12
                next_month = 1 if is_december else month + 1
                next_year = year + (1 if is_december else 0)
                end_date = date(next_year, next_month, 1) - timedelta(days=1)
                end_week = end_date.isocalendar()[1]
                end_year = end_date.isocalendar()[0]
                # space
                same_year = start_year == end_year
                for delegation_id in all_delegation_ids:
                    if same_year:
                        add_new_weeks(
                            start_week, end_week, start_year,
                            entity_month, delegation_id)
                    else:
                        last_day = date(start_year, 12, 28)
                        add_new_weeks(
                            start_week, last_day.isocalendar()[1], start_year,
                            entity_month, delegation_id)
                        first_day = date(end_year, 1, 4)
                        add_new_weeks(
                            first_day.isocalendar()[1], end_week, end_year,
                            entity_month, delegation_id)
        # space
        EntityWeek.objects.bulk_create(new_weeks)


def generate_months_one_year(year):
    from inai.models import EntityMonth
    from geo.models import Entity
    for agency in Entity.objects.all():
        for month in range(12):
            month += 1
            ye_mo = f"{year}-{month:02d}"
            EntityMonth.objects.get_or_create(
                year_month=ye_mo,
                entity=agency.entity)
            #print("%s-%s" % (agency.id, ye_mo))


def generate_months_agency(acronym):
    from inai.models import EntityMonth
    from geo.models import Entity
    for entity in Entity.objects.filter(acronym=acronym):
        for sum_year in range(6):
            year = sum_year + 2017
            for month in range(12):
                month += 1
                ye_mo = f"{year}-{month:02d}"
                EntityMonth.objects.get_or_create(
                    entity=entity, year_month=ye_mo)
                #print("%s-%s" % (agency.id, ye_mo))

# generate_months_agency("SSEDOMEX")
# generate_months_agency("CRAE")
# generate_months_agency("SSPCDMX")

        
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
    ['UMAE Cardiología C.M.N. Siglo XXI', "DFIMS000580"],
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
