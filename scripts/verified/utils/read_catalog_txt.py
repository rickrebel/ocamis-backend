import re


def generate_agency_delegations():
    from geo.models import Delegation, Agency
    agencies_with_clues = Agency.objects.filter(clues__isnull=False).distinct()
    for agency in agencies_with_clues:
        name = f"{agency.name}"
        Delegation.objects.get_or_create(
            name=name, state=agency.state,
            institution=agency.institution, clues=agency.clues)


def create_provider_by_agency():
    from geo.models import Agency, Provider
    agencies = Agency.objects.all()
    for agency in agencies:
        if agency.clues:
            provider, created = Provider.objects.get_or_create(
                name=agency.name, acronym=agency.acronym, state=agency.state,
                institution=agency.institution,
                population=agency.population or 0, is_clues=True
            )
            clues = agency.clues
            clues.provider = provider
            clues.save()
        elif agency.state:
            provider, created = Provider.objects.get_or_create(
                state=agency.state, institution=agency.institution,
                is_clues=False)
            if created:
                provider.population = agency.population or 0
                state_code = agency.state.code_name.upper().replace(".", "")
                provider.acronym = f"SSA-{state_code}"
                provider.name = f"{agency.institution.name} {agency.state.short_name}"
                provider.save()
        else:
            provider, created = Provider.objects.get_or_create(
                name=agency.institution.name, acronym=agency.acronym,
                institution=agency.institution, population=agency.population or 0,
                is_clues=False)
        agency.provider = provider
        agency.save()


# create_entity_by_agency()


def move_delegation_clues():
    from geo.models import Delegation, CLUES, Provider
    all_delegations = Delegation.objects.all()
    for delegation in all_delegations:
        clues = delegation.clues
        if clues:
            clues.delegation = delegation
            delegation.is_clues = True
            if clues.provider:
                delegation.provider = clues.provider
        elif not delegation.provider:
            try:
                delegation.provider = Provider.objects.get(
                    institution=delegation.institution,
                    state=delegation.state, ent_clues__isnull=True)
            except Provider.DoesNotExist:
                print("Provider not found: ", delegation)
            except Provider.MultipleObjectsReturned:
                print("Multiple delegations found: ", delegation)
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


def assign_provider_to_data_files():
    from geo.models import Provider
    from respond.models import DataFile
    all_providers = Provider.objects.all()
    for provider in all_providers:
        data_files = DataFile.objects.filter(
            petition_file_control__petition__agency__provider=provider)
        data_files.update(provider=provider)


def assign_provider_to_month_agency():
    from geo.models import Provider, Agency
    from inai.models import MonthRecord
    all_agencies = Agency.objects.all()
    for agency in all_agencies:
        provider = agency.provider
        if provider:
            month_agencies = MonthRecord.objects.filter(agency=agency)
            month_agencies.update(provider=provider)


def assign_year_month_to_sheet_files(provider_id):
    from respond.models import DataFile
    import re
    all_data_files = DataFile.objects.filter(
        provider_id=provider_id)
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
    from inai.models import MonthRecord
    from respond.models import SheetFile
    all_year_months = MonthRecord.objects.values_list(
        "year_month", flat=True).distinct()
    for year_month in all_year_months:
        new_ym = year_month[:4] + "-" + year_month[4:]
        month_agencies = MonthRecord.objects.filter(year_month=year_month)
        month_agencies.update(year_month=new_ym)
        sheet_files = SheetFile.objects.filter(year_month=year_month)
        sheet_files.update(year_month=new_ym)


def replace_petition_month_by_months_agency():
    from inai.models import Petition
    all_petitions = Petition.objects.all()
    for petition in all_petitions:
        month_agencies_ids = petition.petition_months.values_list(
            "month_record_id", flat=True)
        petition.month_records.set(month_agencies_ids)


def delete_duplicates_months_agency():
    from inai.models import MonthRecord
    from geo.models import Provider
    all_providers = Provider.objects.all()
    for provider in all_providers:
        all_months_agency = MonthRecord.objects.filter(provider=provider)
        year_months = all_months_agency.order_by("year_month").distinct(
            "year_month")
        year_months = year_months.values_list(
            "year_month", flat=True)
        for year_month in list(year_months):
            month_agencies = MonthRecord.objects.filter(
                provider=provider, year_month=year_month)
            month_agencies = month_agencies.order_by("-id")
            first_month_agency = month_agencies.first()
            if month_agencies.count() > 1:
                month_agencies.exclude(id=first_month_agency.id).delete()


def delete_duplicates_week_records():
    from inai.models import WeekRecord
    from geo.models import Provider
    all_providers = Provider.objects.all()
    for provider in all_providers:
        all_week_records = WeekRecord.objects.filter(provider=provider)
        year_weeks = all_week_records\
            .order_by("year_week", "year_month", "iso_delegation")\
            .distinct("year_week", "year_month", "iso_delegation")\
            .values_list("year_week", "year_month", "iso_delegation")
        for year_week, year_month, iso_delegation in list(year_weeks):
            week_records = WeekRecord.objects.filter(
                provider=provider, year_week=year_week,
                year_month=year_month, iso_delegation=iso_delegation)
            week_records = week_records.order_by("-id")
            first_week_record = week_records.first()
            if week_records.count() > 1:
                week_records.exclude(id=first_week_record.id).delete()


def collection_to_snake_name():
    from data_param.models import Collection
    all_collections = Collection.objects.all()
    for collection in all_collections:
        collection.save()


def assign_year_week_to_week_records():
    from respond.models import TableFile
    from inai.models import WeekRecord
    from respond.models import CrossingSheet
    all_week_records = WeekRecord.objects.all()
    for week_record in all_week_records:
        iso_week = week_record.iso_week
        iso_year = week_record.iso_year
        year_week = f"{iso_year}-{iso_week:02d}"
        week_record.year_week = year_week
        week_record.save()
    all_table_files = TableFile.objects.filter(iso_week__isnull=False)
    for table_file in all_table_files:
        iso_week = table_file.iso_week
        iso_year = table_file.iso_year
        year_week = f"{iso_year}-{iso_week:02d}"
        table_file.year_week = year_week
        table_file.save()


def assign_year_month_to_month_records():
    from inai.models import MonthRecord
    all_month_records = MonthRecord.objects.all()
    for month_record in all_month_records:
        year_month = month_record.year_month
        year, month = year_month.split("-")
        month_record.year = year
        month_record.month = month
        month_record.save()


def save_month_records():
    from inai.models import MonthRecord
    from respond.models import SheetFile
    all_sheet_files = SheetFile.objects.filter(
        month_records__isnull=True, year_month__isnull=False)
    for sheet_file in all_sheet_files:
        try:
            month_record = MonthRecord.objects.get(
                provider=sheet_file.data_file.provider, year_month=sheet_file.year_month)
            sheet_file.month_records.add(month_record)
        except MonthRecord.DoesNotExist:
            print("year_month does not exist", sheet_file.year_month)


def assign_entity_to_delegations():
    from geo.models import Provider
    from geo.models import Delegation
    all_delegations = Delegation.objects.filter(
        provider__isnull=True, is_clues=False)
    for delegation in all_delegations:
        institution = delegation.institution
        try:
            provider = Provider.objects.get(institution=institution)
            delegation.provider = provider
            delegation.save()
        except Exception as e:
            print(e)


def move_sheets_to_status(file_control_id):
    from respond.models import SheetFile
    from respond.models import Behavior
    behavior_merge = Behavior.objects.get(name="need_merge")
    sheet_files = SheetFile.objects.filter(
        data_file__petition_file_control_id=file_control_id)
    sheet_files.update(behavior=behavior_merge)


def analyze_every_months(provider_id):
    from inai.misc_mixins.month_record_mix import FromAws
    from inai.models import MonthRecord
    all_months = MonthRecord.objects.filter(provider_id=provider_id)
    for month in all_months:
        from_aws = FromAws(month)
        from_aws.save_month_analysis_prev()


def send_week_records_to_rebuild(limit=None):
    import time
    from scripts.common import build_s3
    # from task.views import build_task_params
    from task.serverless import async_in_lambda
    from data_param.models import Collection
    from respond.models import TableFile
    from django.contrib.auth.models import User
    drug_collection = Collection.objects.get(model_name="Drug")
    # all_table_files = TableFile.objects.filter(
    #     collection=drug_collection,
    #     week_record__isnull=False,
    #     drugs_count=0)
    all_table_files = TableFile.objects.filter(
        collection=drug_collection,
        week_record__isnull=False,
        week_record_id__in=[31002, 36680],
        # week_record__month_record_id=470,
        # drugs_count=1,
        # drugs_count__gt=0,
        # week_record__async_tasks__errors__icontains="extra data after last expected"
    )\
        .distinct()
    # .exclude(week_record__async_tasks__task_function_id="rebuild_week_csv")\
    # week_record__async_tasks__task_function_id=True)
    if limit:
        all_table_files = all_table_files[:limit]
    print("table_files", all_table_files.count())
    # return None
    # class RequestClass:
    #     def __init__(self):
    #         self.user = User.objects.get(username="rickrebel@gmail.com")
    # request = RequestClass()
    # key_task, task_params = build_task_params(
    #     week_record, "rebuild_week_csv", request)
    for table_file in all_table_files:
        week_record = table_file.week_record
        if week_record:
            params = {
                "final_path": table_file.file.name,
                "s3": build_s3(),
                "week_record_id": week_record.id,
            }
            task_params = {
                "models": [week_record]
            }
            async_in_lambda("rebuild_week_csv", params, task_params)


# send_week_records_to_rebuild()


def delete_duplicate_table_files():
    from respond.models import TableFile
    # from data_param.models import Collection
    all_table_files = TableFile.objects\
        .filter(
            drugs_count=0, week_record__isnull=False,
            collection__isnull=False)\
        .prefetch_related("week_record", "week_record__provider")
    print("all_table_files", all_table_files.count())
    for table_file in all_table_files:
        if table_file.provider != table_file.week_record.provider:
            table_file.delete()


def delete_table_files_without_week_record():
    from respond.models import TableFile
    all_table_files = TableFile.objects\
        .filter(
            week_record__isnull=True,
            collection__isnull=False)
    print("all_table_files", all_table_files.count())
    # !!!! ERROOOOOOR
    # all_table_files.delete()


def sum_one_to_drug_table_files():
    from data_param.models import Collection
    from respond.models import TableFile
    drug_collection = Collection.objects.get(model_name="Drug")
    all_table_files = TableFile.objects.filter(
        collection=drug_collection,
        week_record__isnull=False)
    for table_file in all_table_files:
        table_file.drugs_count = table_file.drugs_count + 1
        table_file.save()


def delete_week_records_with_zero():
    from respond.models import TableFile
    from inai.models import WeekRecord
    from data_param.models import Collection
    drug_collection = Collection.objects.get(model_name="Drug")
    need_delete = 0
    table_files = TableFile.objects.filter(
        drugs_count=0, week_record__isnull=False,
        collection=drug_collection)
    for table_file in table_files:
        week_record = table_file.week_record
        avoid = False
        if week_record.last_transformation and week_record.last_crossing:
            if week_record.last_transformation < week_record.last_crossing:
                avoid = True
        if not avoid:
            table_files = week_record.table_files.all()
            if table_files.count() != 2:
                print("week_record_id", week_record.id)
                print("count", table_files.count())
            else:
                need_delete += 1
                # print("week_record_id", week_record.id)
                # table_files.delete()
    print("need_delete", need_delete)


def rebuild_week_records():
    from inai.models import MonthRecord
    from inai.models import WeekRecord
    from django.db.models import Sum
    sum_fields = [
        "drugs_count", "rx_count", "duplicates_count", "shared_count"]
    # SPACE
    def recalculate_month_record(month_record):
        query_sums = [Sum(field) for field in sum_fields]
        result_sums = month_record.weeks.all().aggregate(*query_sums)
        for field_1 in sum_fields:
            setattr(month_record, field_1, result_sums[field_1 + "__sum"])
        month_record.save()
    # SPACE
    fields = [
        # ["drugs_count", "drugs_count"],
        # ["rx_count", "rx_count"],
        ["duplicates_count", "dupli"],
        ["shared_count", "shared"]
    ]
    month_records = set()
    week_records = WeekRecord.objects.filter(
        last_crossing__isnull=False, rx_count__gt=0)
    for week_record in week_records:
        first_task = week_record.async_tasks\
            .filter(status_task_id='finished').first()
        if first_task:
            week_counts = first_task.result.get("month_week_counts")
            if not week_counts:
                continue
            for field in fields:
                setattr(week_record, field[0], week_counts[field[1]])
            week_record.save()
            month_records.add(week_record.month_record_id)
    month_records = MonthRecord.objects.filter(id__in=list(month_records))
    for ent_month in month_records:
        recalculate_month_record(ent_month)


def revert_own_mistake():
    from respond.models import TableFile
    from respond.models import SheetFile
    from data_param.models import Collection
    import time
    def save_model_files(lapsheet, model_paths):
        provider = lapsheet.sheet_file.data_file.provider
        new_table_files = []
        for result_file in model_paths:
            model_name = result_file.get("model")
            if model_name == "Prescription":
                model_name = "Rx"
            query_create = {"provider": provider, "file": result_file["path"]}
            collection = Collection.objects.get(model_name=model_name)
            query_create["collection"] = collection
            query_create["lap_sheet"] = lapsheet
            table_file = TableFile(**query_create)
            new_table_files.append(table_file)
        TableFile.objects.bulk_create(new_table_files)
    total_count = 0
    all_sheet_files = SheetFile.objects.filter(
        async_tasks__status_task_id="finished",
        async_tasks__task_function="start_build_csv_data",
        async_tasks__result__icontains='is_prepare": false')
    print("all_sheet_files", all_sheet_files.count())
    for x in range(14):
        for sheet_file in all_sheet_files[x * 500:(x + 1) * 500]:
            tasks = sheet_file.async_tasks.filter(
                status_task_id="finished",
                task_function="start_build_csv_data",
                result__icontains='is_prepare": false')
            first_task = tasks.first()
            if not first_task:
                continue
            total_count += 1
            final_paths = first_task.result.get("final_paths", [])
            paths_with_model = [path for path in final_paths if path.get("model")]
            lap_sheet = sheet_file.laps.filter(lap=0).first()
            try:
                save_model_files(lap_sheet, paths_with_model)
            except Exception as e:
                print("task_id", first_task.id)
                print("error", e)
        print("--------------")
        print("x", x)
        time.sleep(5)
    print("total_count", total_count)


def revert_own_mistake2():
    from respond.models import TableFile
    from respond.models import SheetFile
    from data_param.models import Collection
    import time
    count_fields = ["drugs_count", "rx_count"]
    # space
    def save_tables_counts(table_file, model_paths):
        query_update = { "file": result_file["path"] }
        for field in count_fields:
            query_update[field] = result_file.get(field, 0)
        table_file.__dict__.update(**query_update)
    total_count = 0
    all_sheet_files = SheetFile.objects.filter(
        async_tasks__status_task_id="finished",
        rx_count=0,
        async_tasks__task_function="start_build_csv_data",
        async_tasks__result__icontains='is_prepare": false').distinct()
    print("all_sheet_files", all_sheet_files.count())
    for x in range(14):
        for sheet_file in all_sheet_files[x * 100:(x + 1) * 100]:
            tasks = sheet_file.async_tasks.filter(
                status_task_id="finished",
                task_function="start_build_csv_data",
                result__icontains='is_prepare": false')
            first_task = tasks.first()
            if not first_task:
                continue
            total_count += 1
            final_paths = first_task.result.get("final_paths", [])
            paths_without_model = [path for path in final_paths if not path.get("model")]
            lap_sheet = sheet_file.laps.filter(lap=0).first()
            try:
                save_tables_counts(lap_sheet, paths_with_model)
            except Exception as e:
                print("task_id", first_task.id)
                print("error", e)
        print("--------------")
        print("x", x)
        time.sleep(5)
    print("total_count", total_count)


def receive_specific_task(task_id="start_build_csv_data"):
    from respond.models import SheetFile
    from task.serverless import async_in_lambda
    from task.models import AsyncTask
    all_sheet_files = SheetFile.objects.filter()


def revert_duplicates_table_files():
    from respond.models import TableFile
    from django.db.models import Count
    table_sums = TableFile.objects.filter(
        collection__isnull=False, lap_sheet__lap=0).values(
        "collection_id", "lap_sheet").annotate(
        count=Count("id")).filter(count__gt=1)
    for table_sum in table_sums:
        table_files = TableFile.objects.filter(
            collection_id=table_sum["collection_id"],
            lap_sheet=table_sum["lap_sheet"])
        first_table_file = table_files.first()
        table_files.exclude(id=first_table_file.id).delete()


def reassign_default_stage(first_stage="initial"):
    from inai.models import MonthRecord
    default_month_records = MonthRecord.objects.filter(
        stage_id=first_stage)
    default_month_records.update(stage_id="init_month")


def calculate_real_stage():
    from inai.models import MonthRecord
    month_records = MonthRecord.objects.filter(
        last_crossing__isnull=False)
    for month_record in month_records:
        if month_record.last_merge:
            if month_record.last_crossing < month_record.last_merge:
                month_record.stage_id = "merge"
            else:
                month_record.stage_id = "analysis"
        elif month_record.last_crossing and month_record.last_transformation:
            if month_record.last_transformation < month_record.last_crossing:
                month_record.stage_id = "analysis"
        month_record.save()


def comprobate_table_insert_when_pre_insert():
    from inai.models import WeekRecord
    week_records = WeekRecord.objects.filter(
        last_pre_insertion__isnull=False,
        table_files__collection__isnull=False,
        table_files__inserted=False)
    for week_record in week_records:
        week_record.table_files.filter(
            collection__isnull=False, inserted=False).update(
            inserted=True)


def rename_task_function(original_name, new_name):
    from task.models import AsyncTask
    AsyncTask.objects.filter(
        task_function_id=original_name).update(
        task_function_id=new_name)

# rename_task_function("analysis_month", "send_analysis")

# assign_year_month_to_sheet_files(53)
# move_delegation_clues()
# delete_insabi_delegations()


def get_bad_inserted():
    from respond.models import TableFile
    from django.db import connection
    from django.db.models import F
    cursor = connection.cursor()
    drugs_in_csvs = TableFile.objects.filter(
        collection__model_name="Drug",
        drugs_count__gt=0,
        week_record__month_record__last_insertion__isnull=False) \
        .values("week_record_id", "drugs_count", "provider_id",
                "week_record__month_record__year_month") \
        .annotate(year_month=F("week_record__month_record__year_month"))
    objects_in_csvs = {drug["week_record_id"]: drug for drug in drugs_in_csvs}
    errors = []
    count_query = f"""
        SELECT week_record_id, count 
        FROM week_record_count;
    """
    cursor.execute(count_query)
    week_counts_in_db = cursor.fetchall()
    print("week_counts_in_db", len(week_counts_in_db))
    cursor.close()
    connection.close()
    result = {
        "not_founded_weeks": [],
        "below_saved": [],
        "below_saved_details": [],
        "above_saved": [],
        "above_saved_details": [],
        "weeks_not_in_db": [],
        "failed_month_records": {},
    }
    def add_failed_week(week_obj, type_error):
        result[type_error].append(week_obj["week_record_id"])
        month_record = f"{week_obj['provider_id']}-{week_obj['year_month']}"
        if month_record not in result["failed_month_records"]:
            result["failed_month_records"][month_record] = {}
        if type_error not in result["failed_month_records"][month_record]:
            result["failed_month_records"][month_record][type_error] = 0
        result["failed_month_records"][month_record][type_error] += 1
    weeks_in_db = [week_db[0] for week_db in week_counts_in_db if week_db[1]]
    for week_csv in drugs_in_csvs:
        if week_csv["week_record_id"] not in weeks_in_db:
            add_failed_week(week_csv, "weeks_not_in_db")
    for week_id, count_in_db in week_counts_in_db:
        if not count_in_db:
            continue
        try:
            week_in_csv = objects_in_csvs[week_id]
            # week_in_csv = drugs_in_csvs.get(week_record_id=week_id)
            count_in_csv = week_in_csv["drugs_count"]
            if count_in_csv > count_in_db:
                add_failed_week(week_in_csv, "below_saved")
                result["below_saved_details"].append(
                    {week_id: f"{count_in_csv} vs {count_in_db}"})
            elif count_in_csv < count_in_db:
                add_failed_week(week_in_csv, "above_saved")
                result["above_saved_details"].append(
                    {week_id: f"{count_in_csv} vs {count_in_db}"})
        except KeyError:
            result["not_founded_weeks"].append(week_id)
    for counter, value in result.items():
        print(counter, len(value))
    return result


def generate_report_inserted():
    bad_inserted = get_bad_inserted()
    failed_months = bad_inserted["failed_month_records"]
    sorted_failed_months = sorted(
        failed_months.items(), key=lambda x: x[0], reverse=False)
    for key, value in sorted_failed_months:
        print(key, value)
    return bad_inserted["weeks_not_in_db"]


failed_weeks = generate_report_inserted()
print("failed_weeks", len(failed_weeks))


def insert_failed_weeks(failed_week_ids):
    from formula.views import modify_constraints
    failed_week_ids = failed_weeks
    from django.db import connection
    from inai.misc_mixins.insert_month_mix import InsertMonth
    from respond.models import TableFile
    cursor = connection.cursor()
    queries = {"create": [], "drop": []}
    current_temp_table = "55_temps"
    errors = []
    for table_name in ["rx", "drug"]:
        temp_table = f"fm_{current_temp_table}_{table_name}"
        queries["create"].append(f"""
            CREATE TABLE {temp_table}
            (LIKE formula_{table_name} INCLUDING CONSTRAINTS);
        """)

    def execute_query(query_content):
        try:
            cursor.execute(query_content)
        except Exception as e:
            str_e = str(e)
            if "current transaction is aborted" in str_e:
                return
            errors.append(f"Hubo un error al guardar; {str(e)}")

    for query in queries["create"]:
        execute_query(query)

    month_table_files = TableFile.objects\
        .filter(
            week_record_id__in=failed_week_ids,
            inserted=True)
    print("month_table_files", month_table_files.count())

    first_month_record = month_table_files.first().week_record.month_record
    my_insert_base = InsertMonth(first_month_record)

    queries_by_model = my_insert_base.build_query_tables(
        month_table_files, current_temp_table)

    for model_name, content in queries_by_model.items():
        base_queries = content["base_queries"]
        alternative_query = content.get("alternative_query")
        files = content["files"]
        for query_base in base_queries:
            for idx, path in enumerate(files):
                if idx % 50 == 0:
                    print("idx", idx)
                    print("errors", errors)
                query = query_base.replace("PATH_URL", path)
                execute_query(query)

    print("errors", errors)

    drugs_counts = TableFile.objects.filter(
            week_record_id__in=failed_week_ids,
            collection__model_name="Drug")\
        .values("week_record_id", "drugs_count")
    # drugs_counts = {d["id"]: d["drugs_count"] for d in drugs_counts}
    drugs_counts = list(drugs_counts)
    drugs_object = {drug["week_record_id"]: drug["drugs_count"]
                    for drug in drugs_counts}

    if not drugs_object:
        error = "No se encontraron semanas con medicamentos"
        errors.append(error)

    temp_drug = f"fm_{current_temp_table}_drug"

    count_query = f"""
        SELECT week_record_id,
        COUNT(*)
        FROM {temp_drug}
        GROUP BY week_record_id;
    """

    some_error = False
    cursor.execute(count_query)
    week_counts = cursor.fetchall()

    below_weeks = []
    above_weeks = []
    not_founded_weeks = []
    not_inserted_weeks = []
    week_ids_in_db = set()

    for week_count in week_counts:
        week_id = week_count[0]
        str_week_id = str(week_id)
        week_ids_in_db.add(week_id)
        count = week_count[1]
        week_count = drugs_object.get(week_id)
        if not week_count:
            if count:
                print("week_id 0", week_id)
                some_error = True
        elif week_count == count:
            continue
        elif week_count > count:
            print("week_id 1", week_id)
            some_error = True
        else:
            print("week_id 2", week_id)
            some_error = True

    for week_id, week_count in drugs_object.items():
        if week_id not in week_ids_in_db and week_count:
            print("week_id 3", week_id)
            some_error = True

    if len(not_founded_weeks) > 0:
        print("not_founded_weeks", len(not_founded_weeks))
        some_error = True

    if len(not_inserted_weeks) > 0:
        print("not_inserted_weeks", len(not_inserted_weeks))
        some_error = True

    if len(above_weeks) > 0:
        print("above_weeks", len(above_weeks))
        some_error = True

    if len(below_weeks) > 0:
        print("below_weeks", len(below_weeks))
        some_error = True

    if some_error:
        errors.append("Hubo un error en los conteos")

    print("errors", errors)


    errors = []

    constraint_queries = modify_constraints(True, False, current_temp_table)

    for constraint in constraint_queries:
        try:
            cursor.execute(constraint)
        except Exception as e:
            str_e = str(e)
            if "already exists" in str_e:
                continue
            if "multiple primary keys" in str_e:
                continue
            if "current transaction is aborted" in str_e:
                continue
            print("constraint", constraint)
            print(f"ERROR:\n, {e}, \n--------------------------")
            errors.append(f"Error en constraint {constraint}; {str(e)}")

    insert_queries = []
    drop_queries = []
    for table_name in ["rx", "drug"]:
        temp_table = f"fm_{current_temp_table}_{table_name}"
        insert_queries.append(f"""
            INSERT INTO formula_{table_name}
            SELECT *
            FROM {temp_table};
        """)
        drop_queries.append(f"""
            DROP TABLE IF EXISTS {temp_table} CASCADE;
        """)

    for insert_query in insert_queries:
        execute_query(insert_query)

    for drop_query in drop_queries:
        execute_query(drop_query)

    if errors:
        connection.rollback()
        # errors.append(f"Hubo un error al guardar; {str(e)}")
    else:
        cursor.close()
        connection.commit()
    connection.close()
    print("errors", errors)


def change_month_stage():
    from inai.models import MonthRecord
    MonthRecord.objects.filter(
        stage_id="explore").update(stage_id="init_month")
