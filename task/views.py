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


def build_task_params(model_obj, function_name, request=None, **kwargs):
    subgroup = kwargs.get("subgroup")
    parent_task = kwargs.get("parent_task")
    finished_function = kwargs.get("finished_function")
    keep_tasks = kwargs.get("keep_tasks", False)
    model_name = camel_to_snake(model_obj.__class__.__name__)
    create_kwargs = {model_name: model_obj}
    is_massive = False
    if bool(subgroup):
        create_kwargs["subgroup"] = subgroup
        is_massive = "|" in subgroup

    def update_previous_tasks(tasks):
        tasks = tasks.filter(is_current=True)
        for task in tasks:
            task.is_current = False
            task.save()
            if task.child_tasks.filter(is_current=True).exists():
                update_previous_tasks(task.child_tasks.all())

    if not is_massive and not keep_tasks:
        update_previous_tasks(AsyncTask.objects.filter(**create_kwargs))
    if finished_function:
        create_kwargs["finished_function"] = finished_function
    if is_massive:
        create_kwargs["is_massive"] = True
    task_function, created = TaskFunction.objects.get_or_create(
        name=function_name)
    if created:
        task_function.public_name = f"{function_name} (Creada por excepción)"
        task_function.save()
    if model_name == "data_file":
        stage = task_function.stages.last()
        if stage:
            model_obj.stage = stage
            model_obj.status_id = "pending"
            model_obj.save()

    user = None
    if parent_task:
        create_kwargs["parent_task"] = parent_task
        user = parent_task.user
    elif request:
        user = request.user

    key_task = AsyncTask.objects.create(
        user=user, task_function=task_function,
        date_start=datetime.now(), status_task_id="created", **create_kwargs
    )
    return key_task, {"parent_task": key_task}


def comprobate_status(
        current_task, errors=None, new_tasks=None, want_http_response=False):
    from rest_framework.response import Response
    from rest_framework import status

    # print("comprobate_status", current_task, current_task.id)
    if not current_task:
        raise Exception("No se ha encontrado la tarea enviada")
    if errors:
        current_task.errors = errors
        if isinstance(errors, str):
            status_task_id = "not_executed"
        else:
            status_task_id = "with_errors"
    elif new_tasks:
        status_task_id = "children_tasks"
    else:
        status_task_id = "finished"
    print("status_task_id: ", status_task_id)
    current_task = comprobate_brothers(current_task, status_task_id)
    if want_http_response:
        body_response = {"new_task": current_task.id}
        if errors:
            body_response["errors"] = errors
            return Response(body_response, status=status.HTTP_400_BAD_REQUEST)
        if new_tasks:
            return Response(body_response, status=status.HTTP_200_OK)
        else:
            return None
    comprobate_queue(current_task)
    return current_task


def execute_finished_function(parent_task):
    from task.main_views_aws import AwsFunction
    finished_function = parent_task.finished_function
    brothers_in_finish = AsyncTask.objects.filter(
        parent_task=parent_task,
        task_function_id=finished_function)
    if brothers_in_finish.exists():
        return comprobate_children_with_errors(parent_task)
    # params_after = parent_task.params_after or {}
    # params_finished = params_after.get("params_finished", {})

    class RequestClass:
        def __init__(self):
            self.user = parent_task.user

    req = RequestClass()
    add_elems = {"parent_task": parent_task, "keep_tasks": True}
    model, current_obj = find_task_model(parent_task)
    new_task, task_params = build_task_params(
        current_obj, finished_function, req, **add_elems)
    aws_function = AwsFunction(new_task, parent_task=parent_task)
    new_task2 = aws_function.execute_next_function()
    is_final = new_task2.status_task.is_completed
    return comprobate_children_with_errors(parent_task) \
        if is_final else "children_tasks"


def comprobate_children_with_errors(parent_task):
    children_with_errors = AsyncTask.objects.filter(
        parent_task=parent_task,
        status_task__macro_status="with_errors")
    if children_with_errors.exists():
        return "some_errors"
    else:
        return "finished"


def comprobate_brothers(current_task, status_task_id):
    try:
        current_task = current_task.save_status(status_task_id)
    except Exception as e:
        print("current_task: ", current_task)
        print("ERROR AL GUARDAR: ", e)
    is_final = current_task.status_task.is_completed
    # print(current_task.id, " is_final: ", is_final)
    if is_final and current_task.parent_task:
        parent_task = current_task.parent_task
        brothers_incomplete = AsyncTask.objects.filter(
            parent_task=parent_task,
            status_task__is_completed=False)
        # print("paso por acá comprobando brothers")
        # print("brothers_incomplete: ", brothers_incomplete)
        if brothers_incomplete.exists():
            parent_status_task_id = "children_tasks"
        else:
            # print("finished_function: ", parent_task.finished_function)
            if parent_task.finished_function:
                parent_status_task_id = execute_finished_function(parent_task)
            else:
                # print("llego a finished del padre")
                parent_status_task_id = comprobate_children_with_errors(
                    parent_task)
        comprobate_brothers(parent_task, parent_status_task_id)
    return current_task


def comprobate_queue(current_task):
    from task.serverless import execute_async
    # from django.conf import settings
    # from inai.data_file_mixins.insert_mix import modify_constraints

    # is_queue = current_task.task_function_id in ["save_csv_in_db"]
    # if not is_queue:
    if not current_task.task_function.is_queueable:
        return

    def send_to_execute(tasks):
        for task in tasks:
            execute_async(task, task.original_request)

    if current_task.status_task.is_completed:
        task_function = current_task.task_function
        if task_function.ebs_percent:
            # pending_rds_tasks = AsyncTask.objects.filter(
            #     task_function__ebs_percent__gt=0,
            #     status_task_id="queue")
            pending_rds_tasks = AsyncTask.objects.in_queue(ebs=True)
            if pending_rds_tasks.exists():
                has_balance = has_enough_balance(task_function)
                if has_balance:
                    next_task = pending_rds_tasks.order_by("id").first()
                    execute_async(next_task, next_task.original_request)
                else:
                    delayed_execution(comprobate_waiting_balance, 300)
                    return
            return
        # queue_tasks = AsyncTask.objects.filter(
        #     task_function=task_function,
        #     status_task_id="queue").order_by("id")
        queue_tasks = AsyncTask.objects.in_queue(task_function=task_function)
        if not queue_tasks.exists():
            return
        if task_function.group_queue:
            group_obj = getattr(current_task, task_function.group_queue)
            filter_group = {f"{task_function.group_queue}": group_obj}
            same_group_tasks = queue_tasks.filter(**filter_group)
            if same_group_tasks.exists():
                if task_function.queue_size == 1:
                    next_task = same_group_tasks.order_by("id").first()
                    execute_async(next_task, next_task.original_request)
                else:
                    filter_group["task_function"] = task_function
                    filter_group["status_task_id"] = "running"
                    running_tasks = AsyncTask.objects.filter(**filter_group)
                    remain_tasks = task_function.queue_size - running_tasks.count()
                    if remain_tasks > 0:
                        send_to_execute(same_group_tasks[:remain_tasks])
            else:
                not_started_tasks = queue_tasks.filter(
                    parent_task__status_task_id="created")
                if not not_started_tasks.exists():
                    not_started_tasks = queue_tasks.filter(
                        parent_task__parent_task__status_task_id="created")
                if not_started_tasks.exists():
                    first_task = not_started_tasks.first()
                    execute_async(first_task, first_task.original_request)
                    comprobate_queue(first_task)
        else:
            send_to_execute(queue_tasks[:task_function.queue_size])


def resend_error_tasks(task_function_id="save_csv_in_db", task_id=None):
    from respond.models import TableFile
    from task.models import AsyncTask
    from django.utils import timezone
    from task.serverless import execute_async
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
        execute_async(last_task, request_params)


# resend_error_tasks("save_csv_in_db", "e04f5607-5542-4fee-a7c7-1badb598447a")
