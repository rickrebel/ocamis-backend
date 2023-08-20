
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
    lap_sheets = LapSheet.objects.filter(cat_inserted=True)
    lap_sheets.update(
        missing_inserted=False, cat_inserted=False, inserted=False)
    inserted_table_files = TableFile.objects.filter(inserted=True)
    inserted_table_files.update(inserted=False)
    DataFile.objects.filter(stage_id="insert")\
        .update(stage_id="transform", status_id="finished")
    EntityMonth.objects.filter(last_pre_insertion__isnull=False)\
        .update(last_pre_insertion=None)
    EntityWeek.objects.filter(last_pre_insertion__isnull=False)\
        .update(last_pre_insertion=None)
    EntityMonth.objects.filter(stage_id='pre_insert')\
        .update(stage_id='merge', status_id='finished')
    EntityMonth.objects.filter(stage_id='insert')\
        .update(stage_id='merge', status_id='finished')
    # EntityMonth.objects.filter(last_merge__isnull=False)\
    #     .update(last_merge=None)
    # EntityWeek.objects.filter(last_merge__isnull=False)\
    #     .update(last_merge=None)
    # SheetFile.objects.filter(behavior="merged").update(behavior="need_merge")
    if hard:
        AsyncTask.objects.filter(task_function_id="send_months_to_db").delete()
        AsyncTask.objects.filter(task_function_id="insert_month").delete()
        # AsyncTask.objects.filter(task_function_id="pre_insert_month").delete()
        # AsyncTask.objects.filter(task_function_id="save_csv_in_db").delete()
        # AsyncTask.objects.filter(task_function__is_queueable=True).delete()

# reverse_insert(True)


def save_success_params_after():
    from task.models import AsyncTask
    from inai.models import TableFile
    success_tasks = AsyncTask.objects.filter(
        task_function_id='save_csv_in_db',
        status_task_id="finished")
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


def upload_s3_files(local_file, s3_dir):
    import boto3
    # import boto3.s3.transfer as s3transfer
    from scripts.common import build_s3
    s3 = build_s3()
    print("s3: ", s3)
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=s3["aws_access_key_id"],
        aws_secret_access_key=s3["aws_secret_access_key"],
    )
    # bucket_name = s3["bucket_name"]
    bucket_name = "cdn-desabasto.s3-accelerate.amazonaws.com"
    aws_location = s3["aws_location"]
    s3_file = f"{aws_location}/{s3_dir}{local_file.split('/')[-1]}"
    print("local_file: ", local_file)
    try:
        # s3_client.put_object(
        #     Bucket=bucket_name,
        #     Key=f"{aws_location}/{final_name}",
        #     Body=csv_buffer.getvalue(),
        #     ContentType="text/csv",
        #     ACL="public-read",
        # )
        s3_client.upload_file(local_file, bucket_name, s3_file)
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except Exception as e:
        print("Error: ", e)
        return False


# upload_s3_files = upload_s3_files(
#     'D:\\RecetasIMSS\\req_mayo_2020_02.txt.gz', 'nacional/imss/202107/')

# upload_s3_files2 = upload_s3_files(
#     'C:\\Users\\Ricardo\\Downloads\\req_mayo_2020_02.txt.gz', 'nacional/imss/202107/')


def delete_bad_week(entity_id, year, month, iso_year, iso_week, iso_delegation):
    from datetime import datetime
    from django.db import connection
    from inai.models import EntityMonth, EntityWeek
    errors = []
    entity_week = EntityWeek.objects.filter(
        entity_id=entity_id, year=year, month=month,
        iso_year=iso_year, iso_week=iso_week,
        iso_delegation=iso_delegation).first()
    if not entity_week:
        errors.append("No existe la semana")
        return None, errors
    cursor = connection.cursor()
    drop_queries = []
    # space
    def execute_query(query_content):
        try:
            cursor.execute(query_content)
        except Exception as e:
            str_e = str(e)
            if "current transaction is aborted" in str_e:
                return
            errors.append(f"Hubo un error al guardar; {str(e)}")
    query_1 = f"""
        DELETE FROM formula_rx
        WHERE entity_id = {entity_id} AND year = {year} AND month = {month}  
            AND iso_year = {iso_year} AND iso_week = {iso_week}
            AND iso_delegation = {iso_delegation};
    """
    drop_queries.append(query_1)
    query_2 = f"""
        DELETE FROM formula_drug
        WHERE entity_week_id = {entity_week.id};
    """
    drop_queries.append(query_2)
    # for drop_query in drop_queries:
    #     print("drop_query", drop_query)
    #     print("before drop_query", datetime.now())
    #     if not errors:
    #         execute_query(drop_query)
    print("errors", errors)
    # print("end", datetime.now())
    if errors:
        connection.rollback()
        # errors.append(f"Hubo un error al guardar; {str(e)}")
    else:
        cursor.close()
        connection.commit()
    print("end 2", datetime.now())
    connection.close()
    return drop_queries, errors


# queries, errs = delete_bad_week(55, 2018, 11, 2018, 46, 247)


def delete_bad_month(year, month, entity_id=55):
    from datetime import datetime
    from django.db import connection
    from inai.models import EntityMonth
    errors = []
    cursor = connection.cursor()
    drop_queries = []
    # space
    def execute_query(query_content):
        try:
            cursor.execute(query_content)
        except Exception as e:
            str_e = str(e)
            if "current transaction is aborted" in str_e:
                return
            errors.append(f"Hubo un error al guardar; {str(e)}")
    query_1 = f"""
        DELETE FROM formula_rx
        WHERE entity_id = {entity_id} AND year = {year} AND month = {month};
    """
    drop_queries.append(query_1)
    year_month = f"{year}-{month:02}"
    entity_m = EntityMonth.objects.get(
        entity_id=entity_id, year_month=year_month)
    all_weeks = entity_m.weeks.all().values_list("id", flat=True)
    query_2 = f"""
        DELETE FROM formula_drug
        WHERE entity_week_id IN {tuple(all_weeks)}
    """
    # drop_queries.append(query_2)
    sheet_files = entity_m.sheet_files.all().values_list("id", flat=True)
    query_3 = f"""
        SELECT uuid 
        FROM formula_missingrow
        WHERE sheet_file_id IN {tuple(sheet_files)};
    """
    cursor.execute(query_3)
    all_uuids = [uuid for uuid, in cursor.fetchall()]
    print("all_uuids", all_uuids)
    query_4 = f"""
        DELETE FROM formula_missingrow
        WHERE sheet_file_id IN {tuple(sheet_files)};
    """
    drop_queries.append(query_4)
    if all_uuids:
        query_5 = f"""
            DELETE FROM formula_missingfield 
            WHERE missing_row_id IN {tuple(all_uuids)};
        """
        drop_queries.append(query_5)
    for drop_query in drop_queries:
        print("drop_query", drop_query)
        print("before drop_query", datetime.now())
        execute_query(drop_query)
    print("errors", errors)
    print("end", datetime.now())
    if errors:
        connection.rollback()
        # errors.append(f"Hubo un error al guardar; {str(e)}")
    else:
        cursor.close()
        connection.commit()
    print("end 2", datetime.now())
    connection.close()


# delete_bad_month(2018, 11)
