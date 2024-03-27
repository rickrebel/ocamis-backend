
def reverse_transform(only_count=False, provider=None, every_files=False):
    from respond.models import LapSheet
    from respond.models import DataFile
    finished_transform = DataFile.objects.filter(
        stage_id="transform", status_id="finished")
    if provider:
        finished_transform = finished_transform.filter(
            petition_file_control__petition__agency__provider_id=provider)
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
        MonthRecord)
    from respond.models import TableFile
    from inai.models import WeekRecord
    from respond.models import LapSheet
    from respond.models import DataFile
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
    MonthRecord.objects.filter(last_pre_insertion__isnull=False)\
        .update(last_pre_insertion=None)
    WeekRecord.objects.filter(last_pre_insertion__isnull=False)\
        .update(last_pre_insertion=None)
    MonthRecord.objects.filter(stage_id='pre_insert')\
        .update(stage_id='merge', status_id='finished')
    MonthRecord.objects.filter(stage_id='insert')\
        .update(stage_id='merge', status_id='finished')
    # MonthRecord.objects.filter(last_merge__isnull=False)\
    #     .update(last_merge=None)
    # WeekRecord.objects.filter(last_merge__isnull=False)\
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
    from respond.models import TableFile
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
    from respond.models import TableFile
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


def delete_bad_week(provider_id, year, month, iso_year, iso_week, iso_delegation):
    from datetime import datetime
    from django.db import connection
    from inai.models import WeekRecord
    errors = []
    week_record = WeekRecord.objects.filter(
        provider_id=provider_id, year=year, month=month,
        iso_year=iso_year, iso_week=iso_week,
        iso_delegation=iso_delegation).first()
    if not week_record:
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
        WHERE provider_id = {provider_id} AND year = {year} AND month = {month}  
            AND iso_year = {iso_year} AND iso_week = {iso_week}
            AND iso_delegation = {iso_delegation};
    """
    drop_queries.append(query_1)
    query_2 = f"""
        DELETE FROM formula_drug
        WHERE week_record_id = {week_record.id};
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


def delete_bad_month(year, month, provider_id=55):
    from datetime import datetime
    from django.db import connection
    from inai.models import MonthRecord
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
        WHERE provider_id = {provider_id} AND year = {year} AND month = {month};
    """
    drop_queries.append(query_1)
    year_month = f"{year}-{month:02}"
    m_record = MonthRecord.objects.get(
        provider_id=provider_id, year_month=year_month)
    all_weeks = m_record.weeks.all().values_list("id", flat=True)
    query_2 = f"""
        DELETE FROM formula_drug
        WHERE week_record_id IN {tuple(all_weeks)}
    """
    drop_queries.append(query_2)
    sheet_files = m_record.sheet_files.all().values_list("id", flat=True)
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


# delete_bad_month(2023, 1, 53)


def copy_export_sql_aws(path, model_in_db, columns_join, query):
    from django.conf import settings
    ocamis_db = getattr(settings, "DATABASES", {}).get("default")
    bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
    aws_location = getattr(settings, "AWS_LOCATION")
    region_name = getattr(settings, "AWS_S3_REGION_NAME")
    access_key = getattr(settings, "AWS_ACCESS_KEY_ID")
    secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
    return f"""
        SELECT aws_s3.query_export_to_s3(
            '{query}',
            '{columns_join}',
            '(format csv, header true, delimiter "|", encoding "UTF8")',
            '{bucket_name}',
            '{aws_location}/{path}',
            '{region_name}',
            '{access_key}',
            '{secret_key}'
        )
    """


def backup_materialized_view(materialized_view_name):
    from django.db import connection
    from datetime import datetime
    cursor = connection.cursor()
    query = f"SELECT * FROM {materialized_view_name}"
    cursor.execute(query)
    all_data = cursor.fetchall()
    print("all_data", all_data)
    print("end", datetime.now())
    cursor.close()
    connection.close()


# from django.conf import settings
# from django.db import connection
# from datetime import datetime
# materialized_view_name = "med_cat_delivered"
# bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
# cursor = connection.cursor()
# # query = f"SELECT aws_commons.create_s3_uri('{bucket_name}', 'cat_images/ejemplo.csv')"
#
# query = f"""
#     SELECT * from aws_s3.query_export_to_s3(
#         'SELECT * FROM med_cat_delivered',
#         'cdn-desabasto',
#         'cat_images/ejemplo4.csv'
#     )
# """
# cursor.execute(query)
# all_data = cursor.fetchall()
# print("all_data", all_data)
# print("end", datetime.now())
# cursor.close()
# connection.close()


def insert_id_to_csv(snake_name):
    from scripts.common import build_s3
    from task.serverless import async_in_lambda
    prev_path = "mat_views"
    params = {
        "final_path": f"{prev_path}/mother_{snake_name}.csv",
        "result_path": f"{prev_path}/mat_{snake_name}.csv",
        "s3": build_s3(),
        "is_enumerate": True
    }
    task_params = {
        "models": []
    }
    async_in_lambda("rebuild_week_csv", params, task_params)


def save_mat_view_in_db(model_name, model_in_db):
    from django.db import connection
    from respond.data_file_mixins.matches_mix import field_of_models
    from inai.misc_mixins.insert_month_mix import build_copy_sql_aws
    columns = field_of_models({"model": model_name, "app": "formula"})
    # column_names = [column["name"].replace("_total", "") for column in columns]
    column_names = [column["name"] for column in columns]
    columns_join = ",".join(column_names)
    final_path = f"mat_views/{model_in_db}.csv"
    sql_copy = build_copy_sql_aws(final_path, model_in_db, columns_join)
    cursor = connection.cursor()
    cursor.execute(sql_copy)
    cursor.close()
    connection.close()


def sent_mat_view_to_table(model_name):
    from task.serverless import camel_to_snake
    # model_name = "DrugPriority"
    snake_simple_name = camel_to_snake(model_name)
    final_model_name = f"Mat{model_name}"
    # save_mat_view_in_db("MatDrugTotals", "mat_drug_totals")
    # insert_id_to_csv(snake_simple_name)
    save_mat_view_in_db(final_model_name, f"mat_{snake_simple_name}")


# sent_mat_view_to_table("DrugPriority")


def make_public_final_fields(collection_name):
    from data_param.models import FinalField
    final_fields = FinalField.objects.filter(
        collection__model_name=collection_name)
    final_fields.update(included_code="complete")
