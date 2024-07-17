from datetime import datetime
from classify_task.models import TaskFunction
from task.models import AsyncTask

from task.rds_balance import (
    has_enough_balance, delayed_execution, comprobate_waiting_balance)


def find_task_model(async_task):
    task_models = [
        "petition", "file_control", "reply_file", "sheet_file",
        "data_file", "week_record", "month_record", "cluster",
        "mat_view"]
    for model in task_models:
        current_obj = getattr(async_task, model)
        if current_obj:
            return model, current_obj


def camel_to_snake(name):
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def resend_error_tasks(task_function_id="save_csv_in_db", task_id=None):
    from respond.models import TableFile
    from task.models import AsyncTask
    from django.utils import timezone
    # from task.serverless import execute_async
    error_tasks = AsyncTask.objects.filter(
        task_function_id=task_function_id,
        status_task__macro_status="with_errors")
    sent_tasks = AsyncTask.objects.filter(
        task_function_id=task_function_id,
        status_task_id="running")
    all_tasks = error_tasks | sent_tasks
    if task_id:
        all_tasks = all_tasks.filter(request_id=task_id)
    last_task = None
    for task in all_tasks:
        errors = "\n".join(task.errors)
        if "Ya se había insertado" in task.errors:
            task.delete()
            continue
        elif "extra data after last expected column" in errors:
            continue
        elif "HTTP 416. Check your arguments and try again" in errors:
            continue
        else:
            print("task_id: ", task.request_id or task.id)
            print("errors: ", task.errors)
            if task.status_task_id == "running":
                task.status_task_id = "with_errors"
                task.errors = ["Nunca se envío, se elimina manualmente"]
                task.save()
            table_files_ids = task.params_after.get("table_files_ids", [])
            table_files = TableFile.objects.filter(id__in=table_files_ids)
            inserted_count = table_files.filter(inserted=True).count()
            if inserted_count == len(table_files):
                task.status_task_id = "finished"
                task.save()
                continue
            if task.week_record:
                print("last_pre_insertion:", task.week_record.last_pre_insertion)
            else:
                print("no hay week_record")
            print("-------------------------")
            new_task = task
            new_task.pk = None
            new_task.save()
            new_task.status_task_id = "queue"
            new_task.result = None
            new_task.errors = None
            new_task.date_start = timezone.now()
            new_task.date_arrive = None
            new_task.date_end = None
            new_task.save()
            last_task = new_task
    if last_task:
        request_params = last_task.original_request.copy()
        request_params["forced_queue"] = True
        # execute_async(last_task, request_params)


# resend_error_tasks("save_csv_in_db", "e04f5607-5542-4fee-a7c7-1badb598447a")
