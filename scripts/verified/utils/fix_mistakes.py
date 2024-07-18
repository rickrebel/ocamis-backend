
def delete_duplicates_months_agency():
    from inai.models import MonthRecord
    from geo.models import Provider
    all_providers = Provider.objects.all()
    for provider in all_providers:
        all_months_agency = MonthRecord.objects.filter(provider=provider)
        year_months = all_months_agency\
            .order_by("year_month").distinct("year_month")
        year_months = year_months.values_list(
            "year_month", flat=True)
        for year_month in list(year_months):
            month_agencies = MonthRecord.objects.filter(
                provider=provider, year_month=year_month)
            month_agencies = month_agencies.order_by("-id")
            first_month_agency = month_agencies.first()
            if month_agencies.count() > 1:
                month_agencies.exclude(id=first_month_agency.id).delete()


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
            query_create = { "provider": provider, "file": result_file["path"] }
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
    from respond.models import SheetFile
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
