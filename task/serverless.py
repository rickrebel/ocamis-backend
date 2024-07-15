import json
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone
from scripts.common import build_s3
from task.models import AsyncTask
from task.aws.common import BotoUtils
from task.rds_balance import (
    has_enough_balance, delayed_execution, comprobate_waiting_balance)
from task.aws.start_build_csv_data import lambda_handler as start_build_csv_data
from task.aws.split_horizontal import lambda_handler as split_horizontal
from task.aws.start_build_csv_data import lambda_handler as prepare_files
from task.aws.save_csv_in_db import lambda_handler as save_csv_in_db
from task.aws.insert_temp_tables import lambda_handler as insert_temp_tables
from task.aws.xls_to_csv import lambda_handler as xls_to_csv
from task.aws.decompress_gz import lambda_handler as decompress_gz
from task.aws.analyze_uniques import lambda_handler as analyze_uniques
from task.aws.decompress_zip_aws import lambda_handler as decompress_zip_aws
from task.aws.build_week_csvs import lambda_handler as build_week_csvs
from task.aws.rebuild_week_csv import lambda_handler as rebuild_week_csv

api_url = getattr(settings, "API_URL", False)


def camel_to_snake(name):
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class Serverless:
    errors: list = []

    def __init__(self, main_task: AsyncTask, errors=None, params=None):
        self.main_task = main_task
        if errors:
            self.errors = errors
        else:
            self.errors = []
        self.new_tasks = []
        self.params = {}
        if params:
            self.params = params
        elif main_task.original_request:
            self.params = main_task.original_request

        self.params.update({
            "webhook_url": f"{api_url}task/webhook_aws/",
            "s3": build_s3(),
        })

    def set_function_name(self, function_name=None):

        raise NotImplementedError("set_function_name")

    def save_queue(self):
        if self.main_task.task_function.ebs_percent:
            delayed_execution(comprobate_waiting_balance, 300)
        self.main_task.status_task_id = "queue"
        self.main_task.save()
        return True

    def execute_async(self):
        print("SE VA A EJECUTAR:", self.main_task.task_function_id)
        use_local_lambda = getattr(settings, "USE_LOCAL_LAMBDA", False)
        if use_local_lambda:
            return self.execute_in_local()
        else:
            return self.execute_in_lambda()

    def execute_in_lambda(self):
        s3_client, _ = build_s3()
        function_final = f"{self.main_task.task_function_id}:normal"
        dumb_params = json.dumps(self.params)
        try:
            response = s3_client.invoke(
                FunctionName=function_final,
                InvocationType='Event',
                LogType='Tail',
                Payload=dumb_params
            )
            request_id = response["ResponseMetadata"]["RequestId"]
            self.main_task.request_id = request_id
            self.main_task.status_task_id = "running"
            self.main_task.date_sent = datetime.now()
            self.main_task.save()
            return True
        except Exception as e:
            error = f"ERROR EN LAMBDA: {e}"
            print(error)
            self.main_task.status_task_id = "not_sent"
            self.main_task.errors = [str(e)]
            self.main_task.save()
            return False

    def execute_in_local(self):
        import threading
        function_name = self.main_task.task_function.name
        if not globals().get(function_name, False):
            return self.execute_in_lambda()

        print("SE EJECUTA EN LOCAL:", function_name)
        request_id = self.main_task.id
        self.params["artificial_request_id"] = str(request_id)
        self.main_task.request_id = request_id
        self.main_task.status_task_id = "running"
        self.main_task.save()

        def run_in_thread():
            class Context:
                def __init__(self):
                    self.aws_request_id = request_id
                    self.function_name = f"{function_name} in local"

            globals()[function_name](self.params, Context())

        t = threading.Thread(target=run_in_thread)
        t.start()
        return True


class TaskChecker:

    def __init__(self, main_task: AsyncTask = None):
        self.main_task = main_task

    def debug_all(self):
        success_executed = self.debug_success()
        if not success_executed:
            queue_executed = self.debug_queue()
        self.debug_aged_running()

    def debug_success(self):
        from task.views_main_aws import AwsFunction

        very_recent = timezone.now() - timedelta(seconds=20)
        arrived_tasks = AsyncTask.objects.filter(
            status_task_id="success", date_arrive__lt=very_recent)
        for task in arrived_tasks:
            # if task.date_arrive < very_recent:
            current_task = AwsFunction(main_task=task)
            current_task.execute_next_function(task.function_after)
            if task.sheet_file and current_task.errors:
                stage_name = self.find_stage(task)
                if stage_name:
                    task.sheet_file.save_stage(stage_name, current_task.errors)
        return False

    def debug_queue(self):
        queue_tasks = AsyncTask.objects.in_queue()
        if queue_tasks.exists():
            some = False
            queue_tasks = queue_tasks.exclude(
                task_function__group_queue__isnull=False)
            self._execute_many_tasks(queue_tasks)
            next_group_task = queue_tasks.filter(
                task_function__group_queue__isnull=False).first()
            if next_group_task:
                self.main_task = next_group_task
                group_queue = queue_tasks.filter(
                    task_function=next_group_task.task_function)
                some = self.comprobate_group_queue(group_queue)
            return queue_tasks.exists() or some

    def debug_ebs(self):
        ebs_tasks = AsyncTask.objects.in_queue(ebs=True)
        if ebs_tasks.exists():
            return self.comprobate_ebs(
                want_send=True, ebs_task=ebs_tasks.first())

    def debug_aged_running(self):
        from task.views_main_aws import AwsFunction
        s3 = build_s3()
        s3_utils = BotoUtils(s3)

        fifteen_minutes_ago = timezone.now() - timedelta(minutes=15)
        running_tasks = AsyncTask.objects.filter(
            status_task_id="running", date_sent__lt=fifteen_minutes_ago)
        for task in running_tasks:
            file_path = f"aws_errors/{task.request_id}.json"
            try:
                body = s3_utils.get_json_file(file_path)
            except Exception as e:
                task.status_task_id = "not_sent"
                task.errors = [f"No se guardó en s3 el resultado; {str(e)}"]
                continue
            AwsFunction(body=body)

    def find_stage(self, task):
        stage = task.task_function.stages.first()
        if stage:
            return stage.name
        if task.parent_task:
            return self.find_stage(task.parent_task)
        return None

    def comprobate_queue(self, is_main=False):
        task_function = self.main_task.task_function
        if not task_function.is_queueable:
            return
        if not self.main_task.status_task.is_completed:
            return

        if task_function.ebs_percent:
            return self.comprobate_ebs()

        queue_tasks = AsyncTask.objects.in_queue(task_function=task_function)
        if not queue_tasks.exists():
            return
        if task_function.group_queue:
            self.comprobate_group_queue(queue_tasks)
        else:
            self._execute_first(queue_tasks)
        self._save_main_task()

    def comprobate_ebs(self, want_send=False, ebs_task=None):
        if ebs_task:
            self.main_task = ebs_task
            want_send = True
        else:
            running_rds_tasks = AsyncTask.objects\
                .filter(task_function__ebs_percent__gt=0,
                        status_task_id="running")
            if running_rds_tasks.exists():
                return False
        pending_rds_tasks = AsyncTask.objects.in_queue(
            ebs=True, task_function=self.main_task.task_function)
        if want_send:
            pending_rds_tasks = pending_rds_tasks.exclude(id=self.main_task.id)
        has_pending = pending_rds_tasks.exists()
        task_function = self.main_task.task_function
        if has_pending or want_send:
            has_balance = has_enough_balance(task_function)
            if has_balance:
                if has_pending:
                    return self._execute_first(pending_rds_tasks)
                else:
                    return self._execute_main_task()
            else:
                delayed_execution(comprobate_waiting_balance, 300)
        return False

    def comprobate_group_queue(self, queue_tasks):
        task_function = self.main_task.task_function
        group_queue = getattr(self.main_task, task_function.group_queue)

        filter_group = {f"{task_function.group_queue}": group_queue}
        same_group_tasks = queue_tasks.filter(**filter_group)
        if same_group_tasks.exists():
            if task_function.queue_size == 1:
                return self._execute_first(same_group_tasks)
            filter_group["task_function"] = task_function
            filter_group["status_task_id"] = "running"
            running_tasks = AsyncTask.objects.filter(**filter_group)
            remain_tasks = task_function.queue_size - running_tasks.count()
            if remain_tasks > 0:
                return self._execute_many_tasks(same_group_tasks[:remain_tasks])
        else:
            not_started_tasks = queue_tasks.filter(
                parent_task__status_task_id="created")
            if not not_started_tasks.exists():
                not_started_tasks = queue_tasks.filter(
                    parent_task__parent_task__status_task_id="created")
            if not_started_tasks.exists():
                return self._execute_first(not_started_tasks)
                # first_task = not_started_tasks.first()
                # execute_async(first_task, first_task.original_request)
                # RICK TASK: por qué estamos haciendo esto?
                # first_task_helper = TaskHelper(first_task)
                # first_task_helper.comprobate_queue()

    def _save_main_task(self):
        if self.main_task:
            self.main_task.save()

    def _execute_many_tasks(self, tasks):
        self._save_main_task()
        for task in tasks:
            next_serverless = Serverless(task)
            next_serverless.execute_async()
        return bool(len(tasks))

    def _execute_first(self, tasks):
        self._save_main_task()
        if first_task := tasks.first():
            next_serverless = Serverless(first_task)
            next_serverless.execute_async()
        return True

    def _execute_main_task(self):
        self._save_main_task()
        next_serverless = Serverless(self.main_task)
        return next_serverless.execute_async()


def execute_async(current_task, params):
    import threading
    from scripts.common import start_session

    task_function = current_task.task_function
    function_name = task_function.lambda_function or task_function.name
    # if current_task.task_function.is_queueable and "save" in function_name:
    #     function_name = "save_csv_in_db"
    use_local_lambda = getattr(settings, "USE_LOCAL_LAMBDA", False)
    print("SE VA A EJECUTAR:", function_name)
    if globals().get(function_name, False) and use_local_lambda:
        print("SE EJECUTA EN LOCAL:", function_name)
        request_id = current_task.id
        params["artificial_request_id"] = str(request_id)
        current_task.request_id = request_id
        current_task.status_task_id = "running"
        current_task.save()
        # payload_response = json.loads(response['Payload'].read())
        # print("payload_response", payload_response)
        print("function_name", function_name)

        def run_in_thread():
            class Context:
                def __init__(self):
                    self.aws_request_id = request_id
                    self.function_name = f"{function_name} in local"

            globals()[function_name](params, Context())

        t = threading.Thread(target=run_in_thread)
        t.start()
        return current_task
    else:
        s3_client, _ = start_session("lambda")
        function_final = f"{function_name}:normal"
        dumb_params = json.dumps(params)
        try:
            response = s3_client.invoke(
                FunctionName=function_final,
                InvocationType='Event',
                LogType='Tail',
                Payload=dumb_params
            )
            # print("response", response, "\n")
            request_id = response["ResponseMetadata"]["RequestId"]
            current_task.request_id = request_id
            current_task.status_task_id = "running"
            current_task.date_sent = datetime.now()
            current_task.save()
            # print("SE GUARDÓ BIEN")
            # payload_response = json.loads(response['Payload'].read())
            # print("payload_response", payload_response)
            return current_task
        except Exception as e:
            print("ERROR EN LAMBDA:\n", e)
            current_task.status_task_id = "not_sent"
            current_task.errors = [str(e)]
            current_task.save()
            return None


def async_in_lambda(function_name, params, task_params):
    from task.models import AsyncTask, TaskFunction

    params["webhook_url"] = f"{api_url}task/webhook_aws/"
    params["s3"] = build_s3()
    params["function_name"] = function_name
    task_function = TaskFunction.objects.get(name=function_name)
    function_after = task_params.get("function_after", f"{function_name}_after")
    query_kwargs = {
        # "task_function_id": function_name,
        "task_function": task_function,
        "function_after": function_after,
        "original_request": params,
        "status_task_id": "pending",
        "date_start": datetime.now(),
    }
    for field in ["parent_task", "params_after", "subgroup"]:
        if field in task_params:
            query_kwargs[field] = task_params[field]

    for model in task_params["models"]:
        query_kwargs[camel_to_snake(model.__class__.__name__)] = model

    try:
        final_task = AsyncTask.objects.create(**query_kwargs)
    except Exception as e:
        print("ERROR AL CREAR TASK", e, "\nvars:\n", query_kwargs)
        return None

    def save_and_send(in_queue=False):
        if in_queue:
            final_task.status_task_id = "queue"
            final_task.save()
            return final_task
        else:
            return execute_async(final_task, params)

    if task_function.ebs_percent:
        pending_count = AsyncTask.objects\
            .filter(
                task_function__ebs_percent__gt=0,
                status_task__is_completed=False) \
            .exclude(id=final_task.id).count()
        if pending_count > 0:
            return save_and_send(in_queue=True)
        elif has_enough_balance(task_function):
            return save_and_send(in_queue=False)
        else:
            return save_and_send(in_queue=True)

    elif task_function.is_queueable:
        pending_tasks = AsyncTask.objects\
            .filter(
                task_function__is_queueable=True,
                status_task__is_completed=False,
                task_function=task_function) \
            .exclude(id=final_task.id)
        has_pending = pending_tasks.count() > 0
        if not has_pending:
            return save_and_send()
        if task_function.simultaneous_groups == 1 and has_pending:
            return save_and_send(True)
        group_obj = None
        if task_function.group_queue:
            group_obj = query_kwargs.get(task_function.group_queue, False)
        if not group_obj:
            return save_and_send(True)

        filter_group = {f"{task_function.group_queue}": group_obj}
        group_tasks = pending_tasks.filter(**filter_group)
        many_same_group = group_tasks.count() >= task_function.queue_size
        if many_same_group:
            return save_and_send(True)
        if group_tasks.count() > 0:
            return save_and_send()

        if task_function.simultaneous_groups > 1:
            groups_count = pending_tasks\
                .values(task_function.group_queue)\
                .distinct()\
                .count()
            many_groups = groups_count >= task_function.simultaneous_groups
            if not many_groups:
                return save_and_send()
        # month_record = query_kwargs.get("month_record", False)
        return save_and_send(True)
    else:
        return save_and_send()

