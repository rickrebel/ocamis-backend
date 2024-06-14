
# Borrar todas las delegaciones del INSABI sin clues
def delete_insabi_delegations():
    from geo.models import Delegation, Institution
    insabi = Institution.objects.get(code="INSABI")
    Delegation.objects.filter(institution=insabi, clues__isnull=True).delete()


def change_month_stage():
    from inai.models import MonthRecord
    MonthRecord.objects.filter(
        stage_id="explore").update(stage_id="init_month")


def collection_to_snake_name():
    from data_param.models import Collection
    all_collections = Collection.objects.all()
    for collection in all_collections:
        collection.save()


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
        from_aws.save_month_analysis()


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


def rebuild_week_records():
    from inai.models import MonthRecord
    from inai.models import WeekRecord
    from django.db.models import Sum
    sum_fields = [
        "drugs_count", "rx_count", "duplicates_count", "shared_count"]

    def recalculate_month_record(month_record):
        query_sums = [Sum(field) for field in sum_fields]
        result_sums = month_record.weeks.all().aggregate(*query_sums)
        for field_1 in sum_fields:
            setattr(month_record, field_1, result_sums[field_1 + "__sum"])
        month_record.save()

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


def send_data_files_to_re_insert(update=False):
    from respond.models import DataFile
    data_files = DataFile.objects\
        .filter(status_id="finished", stage_id="transform")\
        .distinct()
    data_files = data_files.exclude(provider__acronym="ISSSTE")
    print("data_files", data_files.count())
    if update:
        data_files.update(stage_id="pre_transform")


    # 936396


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


# failed_weeks = generate_report_inserted()
# print("failed_weeks", len(failed_weeks))


def insert_failed_weeks(failed_week_ids):
    from formula.views import modify_constraints
    failed_weeks = generate_report_inserted()
    failed_week_ids = failed_weeks
    from django.db import connection
    from inai.misc_mixins.insert_month_mix import InsertMonth
    from respond.models import TableFile
    cursor = connection.cursor()
    queries = {"create": [], "drop": []}
    current_temp_table = "55_temps"
    errors = []
    for table_name in ["rx", "drug"]:
        temp_table = f"tmp.fm_{current_temp_table}_{table_name}"
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

    temp_drug = f"tmp.fm_{current_temp_table}_drug"

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
        temp_table = f"tmp.fm_{current_temp_table}_{table_name}"
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

