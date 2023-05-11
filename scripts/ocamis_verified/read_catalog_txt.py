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


def reverse_transform(only_count=False, agency=None, every_files=False):
    from inai.models import DataFile, LapSheet
    finished_transform = DataFile.objects.filter(
        stage_id="transform", status_id="finished")
    if agency:
        finished_transform = finished_transform.filter(
            petition_file_control__petition__agency_id=agency)
    print("Finished transform: ", finished_transform.count())
    need_reverse = 0
    for data_file in finished_transform:
        if every_files:
            with_missed = LapSheet.objects.filter(
                sheet_file__data_file=data_file, lap=0)
        elif only_count:
            with_missed = LapSheet.objects.filter(
                sheet_file__data_file=data_file, lap=0,
                missing_rows__gt=0, row_errors__icontains="Conteo distinto")
        else:
            with_missed = LapSheet.objects.filter(
                sheet_file__data_file=data_file, lap=0,
                missing_fields__gt=0, missing_rows=0)
        if with_missed.exists():
            need_reverse += 1
            print("data_file: ", data_file)
            data_file.stage_id = "cluster"
            data_file.status_id = "finished"
            data_file.save()
            # with_missed.delete()
    print("Need reverse: ", need_reverse)


# reverse_transform(True, agency=7)


def reverse_insert(hard=False):
    from inai.models import DataFile, TableFile, LapSheet
    from task.models import AsyncTask
    # TableFile.objects.filter(inserted=True).update(inserted=False)
    LapSheet.objects.filter(inserted=True).update(inserted=False)
    LapSheet.objects.filter(inserted=None).update(inserted=False)
    DataFile.objects.filter(stage_id="insert")\
        .update(stage_id="transform", status_id="finished")
    if hard:
        AsyncTask.objects.filter(task_function_id="save_csv_in_db").delete()
        AsyncTask.objects.filter(task_function_id="insert_data").delete()


def categorize_clean_functions():
    from data_param.models import CleanFunction
    valid_control_trans = [
        "include_tabs_by_name", "exclude_tabs_by_name",
        "include_tabs_by_index", "exclude_tabs_by_index",
        "only_cols_with_headers", "no_valid_row_data"]
    CleanFunction.objects.filter(
        name__in=valid_control_trans).update(ready_code="ready")
    valid_column_trans = [
        "fragmented", "concatenated", "format_date", "clean_key_container",
        "get_ceil", "only_params_parent", "only_params_child",
        "global_variable", "text_nulls", "almost_empty", "same_separator",
        "simple_regex"]
    CleanFunction.objects.filter(
        name__in=valid_column_trans).update(ready_code="ready")
    functions_alone = [
        "fragmented", "concatenated", "only_params_parent",
        "only_params_child", "text_nulls", "same_separator",
        "simple_regex", "almost_empty", "format_date"]
    CleanFunction.objects.filter(
        name__in=functions_alone).update(ready_code="ready_alone")


def assign_entity_to_data_files():
    from geo.models import Entity
    from inai.models import DataFile
    all_entities = Entity.objects.all()
    for entity in all_entities:
        data_files = DataFile.objects.filter(
            petition_file_control__petition__agency__entity=entity)
        data_files.update(entity=entity)


def assign_entity_to_month_agency():
    from geo.models import Entity, Agency
    from inai.models import MonthAgency
    all_agencies = Agency.objects.all()
    for agency in all_agencies:
        entity = agency.entity
        if entity:
            month_agencies = MonthAgency.objects.filter(agency=agency)
            month_agencies.update(entity=entity)


def assign_year_month_to_sheet_files(entity_id):
    from inai.models import DataFile
    import re
    all_data_files = DataFile.objects.filter(
        entity_id=entity_id)
    regex_year_month = re.compile(r"_(20\d{4})")
    for data_file in all_data_files:
        file_name = data_file.file.url.split("/")[-1]
        year_month = regex_year_month.search(file_name)
        if year_month:
            year_month_str = year_month.group(1)
            year_month_str = year_month_str[:4] + "-" + year_month_str[4:]
            data_file.sheet_files.update(year_month=year_month_str)
        else:
            continue


def add_line_to_year_months():
    from inai.models import MonthAgency, SheetFile
    all_year_months = MonthAgency.objects.values_list(
        "year_month", flat=True).distinct()
    for year_month in all_year_months:
        new_ym = year_month[:4] + "-" + year_month[4:]
        month_agencies = MonthAgency.objects.filter(year_month=year_month)
        month_agencies.update(year_month=new_ym)
        sheet_files = SheetFile.objects.filter(year_month=year_month)
        sheet_files.update(year_month=new_ym)


# assign_year_month_to_sheet_files(53)





# move_delegation_clues()
# delete_insabi_delegations()


# unknown	Desconocido	True
# partial	Parcialmente	No se entregaron todos los archivos	True
# denied	Negada	No se dieron los medicamentos recetados	True
# complete	Completa	Efectivamente entregada	True
# unavailable	No disponible	No existió información para calcularlo	True
