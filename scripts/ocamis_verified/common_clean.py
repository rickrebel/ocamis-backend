
def reverse_transform(only_count=False, entity=None, every_files=False):
    from inai.models import DataFile, LapSheet, TableFile
    finished_transform = DataFile.objects.filter(
        stage_id="transform", status_id="finished")
    if entity:
        finished_transform = finished_transform.filter(
            petition_file_control__petition__agency__entity_id=entity)
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
# reverse_transform(False, 53, True)


def reverse_insert(hard=False):
    from inai.models import (
        DataFile, TableFile, LapSheet, EntityMonth, EntityWeek, SheetFile)
    from task.models import AsyncTask
    # TableFile.objects.filter(inserted=True).update(inserted=False)
    LapSheet.objects.filter(inserted=True).update(inserted=False)
    LapSheet.objects.filter(inserted=None).update(inserted=False)
    lap_sheets = LapSheet.objects.filter(cat_inserted=True)
    lap_sheets.update(
        missing_inserted=False, cat_inserted=False, inserted=False)
    inserted_table_files = TableFile.objects.filter(inserted=True)
    inserted_table_files.update(inserted=False)
    # TableFile.objects.update(inserted=False)
    DataFile.objects.filter(stage_id="insert")\
        .update(stage_id="transform", status_id="finished")
    EntityMonth.objects.filter(last_insertion__isnull=False)\
        .update(last_insertion=None)
    EntityWeek.objects.filter(last_insertion__isnull=False)\
        .update(last_insertion=None)
    # EntityMonth.objects.filter(last_merge__isnull=False)\
    #     .update(last_merge=None)
    # EntityWeek.objects.filter(last_merge__isnull=False)\
    #     .update(last_merge=None)
    # SheetFile.objects.filter(behavior="merged").update(behavior="need_merge")
    if hard:
        AsyncTask.objects.filter(task_function_id="send_months_to_db").delete()
        AsyncTask.objects.filter(task_function_id="insert_data").delete()
        AsyncTask.objects.filter(task_function_id="insert_month").delete()
        AsyncTask.objects.filter(task_function_id="save_csv_in_db").delete()


def save_success_params_after():
    from task.models import AsyncTask
    from inai.models import TableFile
    success_tasks = AsyncTask.objects.filter(
        task_function_id='save_csv_in_db', status_task_id="finished")
    for task in success_tasks:
        params_after = task.params_after or {}
        table_files_ids = params_after.get("table_files_ids", [])
        if not table_files_ids:
            continue
        table_files = TableFile.objects.filter(id__in=table_files_ids)
        table_files.update(inserted=True)


def resend_possible_success():
    from inai.models import TableFile
    table_files_ids = [
        293729, 293728, 293727, 83449, 83334, 83263,
        296677, 296676, 296675, 82636, 82533, 82485]
    table_files = TableFile.objects.filter(id__in=table_files_ids)
    table_files.update(inserted=True)
