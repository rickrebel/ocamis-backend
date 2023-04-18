import re


def get_file_csv(file_path):
    import io
    with io.open(file_path, "r", encoding="latin-1") as file:
        data = file.readlines()
        # rr_data_rows = data.split("\n")
        # headers = rr_data_rows.pop(0)
        # all_headers = headers.split("|")
        # print(all_headers)
        return data


def find_lines_with_regex(file_path="fixture/catalogo_clues_issste.txt"):
    from geo.models import CLUES
    all_lines = get_file_csv(file_path)
    matched_lines = []
    not_found_clues = []
    for line in all_lines:
        # with regex, extract the string like this: "DFIST000312 096-201-00"
        regex_format = r'\s(\w{5}\d{6})\s(\d{3}\-\d{3}\-\d{2})\s'
        match = re.search(regex_format, line)
        if not match:
            continue
        matched_lines.append([match.group(1), match.group(2)])
        try:
            clues = CLUES.objects.get(clues=match.group(1))
            clues.key_issste = match.group(2)
            clues.save()
        except CLUES.DoesNotExist:
            not_found_clues.append(match.group(1))
    return not_found_clues
    # print(matched_lines)


# missing_clues = find_lines_with_regex()

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


def generate_agency_delegations():
    from geo.models import Delegation, Agency
    agencies_with_clues = Agency.objects.filter(clues__isnull=False).distinct()
    for agency in agencies_with_clues:
        name = f"{agency.name}"
        Delegation.objects.get_or_create(
            name=name, state=agency.state,
            institution=agency.institution, clues=agency.clues)


def create_entity_by_agency():
    from geo.models import Agency, Entity
    agencies = Agency.objects.all()
    for agency in agencies:
        if agency.clues:
            entity, created = Entity.objects.get_or_create(
                name=agency.name, acronym=agency.acronym, state=agency.state,
                institution=agency.institution,
                population=agency.population or 0, is_clues=True
            )
            clues = agency.clues
            clues.entity = entity
            clues.save()
        elif agency.state:
            entity, created = Entity.objects.get_or_create(
                state=agency.state, institution=agency.institution,
                is_clues=False)
            if created:
                entity.population = agency.population or 0
                state_code = agency.state.code_name.upper().replace(".", "")
                entity.acronym = f"SSA-{state_code}"
                entity.name = f"{agency.institution.name} {agency.state.short_name}"
                entity.save()
        else:
            entity, created = Entity.objects.get_or_create(
                name=agency.institution.name, acronym=agency.acronym,
                institution=agency.institution, population=agency.population or 0,
                is_clues=False)
        agency.entity = entity
        agency.save()


# create_entity_by_agency()


def move_delegation_clues():
    from geo.models import Delegation, CLUES, Entity
    all_delegations = Delegation.objects.all()
    for delegation in all_delegations:
        clues = delegation.clues
        if clues:
            clues.delegation = delegation
            delegation.is_clues = True
            if clues.entity:
                delegation.entity = clues.entity
        elif not delegation.entity:
            try:
                delegation.entity = Entity.objects.get(
                    institution=delegation.institution,
                    state=delegation.state, ent_clues__isnull=True)
            except Entity.DoesNotExist:
                print("Entity not found: ", delegation)
            except Entity.MultipleObjectsReturned:
                print("Multiple entities found: ", delegation)
        delegation.save()


# Borrar todas las delegaciones del INSABI sin clues
def delete_insabi_delegations():
    from geo.models import Delegation, Institution
    insabi = Institution.objects.get(code="INSABI")
    Delegation.objects.filter(institution=insabi, clues__isnull=True).delete()


def reverse_insert():
    from inai.models import DataFile, TableFile, LapSheet
    TableFile.objects.filter(inserted=True).update(inserted=False)
    LapSheet.objects.filter(inserted=True).update(inserted=False)
    DataFile.objects.filter(stage_id="insert")\
        .update(stage_id="transform", status_id="finished")

# move_delegation_clues()
# delete_insabi_delegations()


# unknown	Desconocido	True
# partial	Parcialmente	No se entregaron todos los archivos	True
# denied	Negada	No se dieron los medicamentos recetados	True
# complete	Completa	Efectivamente entregada	True
# unavailable	No disponible	No existió información para calcularlo	True
