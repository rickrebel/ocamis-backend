
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
        AsyncTask.objects.filter(task_function_id="insert_data").delete()
        AsyncTask.objects.filter(task_function_id="insert_month").delete()
        AsyncTask.objects.filter(task_function_id="pre_insert_month").delete()
        # AsyncTask.objects.filter(task_function_id="save_csv_in_db").delete()
        AsyncTask.objects.filter(task_function__is_queueable=True).delete()

# reverse_insert(True)


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
