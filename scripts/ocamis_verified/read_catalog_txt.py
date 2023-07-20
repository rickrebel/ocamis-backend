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
    from inai.models import EntityMonth
    all_agencies = Agency.objects.all()
    for agency in all_agencies:
        entity = agency.entity
        if entity:
            month_agencies = EntityMonth.objects.filter(agency=agency)
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
    from inai.models import EntityMonth, SheetFile
    all_year_months = EntityMonth.objects.values_list(
        "year_month", flat=True).distinct()
    for year_month in all_year_months:
        new_ym = year_month[:4] + "-" + year_month[4:]
        month_agencies = EntityMonth.objects.filter(year_month=year_month)
        month_agencies.update(year_month=new_ym)
        sheet_files = SheetFile.objects.filter(year_month=year_month)
        sheet_files.update(year_month=new_ym)


def replace_petition_month_by_months_agency():
    from inai.models import Petition
    all_petitions = Petition.objects.all()
    for petition in all_petitions:
        month_agencies_ids = petition.petition_months.values_list(
            "entity_month_id", flat=True)
        petition.entity_months.set(month_agencies_ids)


def delete_duplicates_months_agency():
    from inai.models import EntityMonth
    from geo.models import Entity
    all_entities = Entity.objects.all()
    for entity in all_entities:
        all_months_agency = EntityMonth.objects.filter(entity=entity)
        year_months = all_months_agency.order_by("year_month").distinct(
            "year_month")
        year_months = year_months.values_list(
            "year_month", flat=True)
        for year_month in list(year_months):
            month_agencies = EntityMonth.objects.filter(
                entity=entity, year_month=year_month)
            month_agencies = month_agencies.order_by("-id")
            first_month_agency = month_agencies.first()
            if month_agencies.count() > 1:
                month_agencies.exclude(id=first_month_agency.id).delete()


def delete_duplicates_entity_weeks():
    from inai.models import EntityWeek
    from geo.models import Entity
    all_entities = Entity.objects.all()
    for entity in all_entities:
        all_entity_weeks = EntityWeek.objects.filter(entity=entity)
        year_weeks = all_entity_weeks\
            .order_by("year_week", "year_month", "iso_delegation")\
            .distinct("year_week", "year_month", "iso_delegation")\
            .values_list("year_week", "year_month", "iso_delegation")
        for year_week, year_month, iso_delegation in list(year_weeks):
            entity_weeks = EntityWeek.objects.filter(
                entity=entity, year_week=year_week,
                year_month=year_month, iso_delegation=iso_delegation)
            entity_weeks = entity_weeks.order_by("-id")
            first_entity_week = entity_weeks.first()
            if entity_weeks.count() > 1:
                entity_weeks.exclude(id=first_entity_week.id).delete()


def collection_to_snake_name():
    from inai.models import Collection
    all_collections = Collection.objects.all()
    for collection in all_collections:
        collection.save()


def assign_year_week_to_entity_weeks():
    from inai.models import EntityWeek, TableFile, CrossingSheet
    all_entity_weeks = EntityWeek.objects.all()
    for entity_week in all_entity_weeks:
        iso_week = entity_week.iso_week
        iso_year = entity_week.iso_year
        year_week = f"{iso_year}-{iso_week:02d}"
        entity_week.year_week = year_week
        entity_week.save()
    all_table_files = TableFile.objects.filter(iso_week__isnull=False)
    for table_file in all_table_files:
        iso_week = table_file.iso_week
        iso_year = table_file.iso_year
        year_week = f"{iso_year}-{iso_week:02d}"
        table_file.year_week = year_week
        table_file.save()
    for crossing_sheet in CrossingSheet.objects.filter(
            iso_week__isnull=False):
        iso_week = crossing_sheet.iso_week
        iso_year = crossing_sheet.iso_year
        year_week = f"{iso_year}-{iso_week:02d}"
        crossing_sheet.year_week = year_week
        crossing_sheet.save()


def assign_year_month_to_entity_months():
    from inai.models import EntityMonth
    all_entity_months = EntityMonth.objects.all()
    for entity_month in all_entity_months:
        year_month = entity_month.year_month
        year, month = year_month.split("-")
        entity_month.year = year
        entity_month.month = month
        entity_month.save()


def save_entity_months():
    from inai.models import SheetFile, EntityMonth
    all_sheet_files = SheetFile.objects.filter(
        entity_months__isnull=True, year_month__isnull=False)
    for sheet_file in all_sheet_files:
        try:
            entity_month = EntityMonth.objects.get(
                entity=sheet_file.data_file.entity, year_month=sheet_file.year_month)
            sheet_file.entity_months.add(entity_month)
        except EntityMonth.DoesNotExist:
            print("year_month does not exist", sheet_file.year_month)


def assign_entity_to_delegations():
    from inai.models import Entity
    from geo.models import Delegation
    all_delegations = Delegation.objects.filter(
        entity__isnull=True, is_clues=False)
    for delegation in all_delegations:
        institution = delegation.institution
        try:
            entity = Entity.objects.get(institution=institution)
            delegation.entity = entity
            delegation.save()
        except Exception as e:
            print(e)


def move_sheets_to_status(file_control_id):
    from inai.models import SheetFile, Behavior
    behavior_merge = Behavior.objects.get(name="need_merge")
    sheet_files = SheetFile.objects.filter(
        data_file__petition_file_control_id=file_control_id)
    sheet_files.update(behavior=behavior_merge)


def analyze_every_months(entity_id):
    from inai.misc_mixins.entity_month_mix import FromAws
    from inai.models import EntityMonth
    all_months = EntityMonth.objects.filter(entity_id=entity_id)
    for month in all_months:
        from_aws = FromAws(month)
        from_aws.save_month_analysis_prev()


def send_entity_weeks_to_rebuild(table_file_id=None):
    from data_param.models import Collection
    from inai.models import TableFile, EntityWeek
    from django.contrib.auth.models import User
    from scripts.common import build_s3
    from task.views import build_task_params
    from task.serverless import async_in_lambda
    drug_collection = Collection.objects.get(model_name="Drug")
    all_table_files = TableFile.objects.filter(
        collection=drug_collection, entity_week__isnull=False)
    if table_file_id:
        all_table_files = all_table_files.filter(id=table_file_id)
    print("table_files", all_table_files.count())
    # return None
    class RequestClass:
        def __init__(self):
            self.user = User.objects.get(username="rickrebel@gmail.com")
    # request = RequestClass()
    # key_task, task_params = build_task_params(
    #     entity_week, "rebuild_week_csv", request)
    for table_file in all_table_files:
        entity_week = table_file.entity_week
        if entity_week:
            params = {
                "final_path": table_file.file.name,
                "s3": build_s3(),
                "entity_week_id": entity_week.id,
            }
            task_params = {
                "models": [entity_week]
            }
            async_in_lambda("rebuild_week_csv", params, task_params)


send_entity_weeks_to_rebuild(603990)



# assign_year_month_to_sheet_files(53)
# move_delegation_clues()
# delete_insabi_delegations()
