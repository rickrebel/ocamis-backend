import json
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone
from typing import Any, Optional

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
from task.aws.add_constraint import lambda_handler as add_constraint
from task.aws.add_mat_view import lambda_handler as add_mat_view
from task.aws.save_cat_tables import lambda_handler as save_cat_tables


def camel_to_snake(name):
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class Context:
    def __init__(self, request_id, function_name):
        self.aws_request_id = request_id
        self.function_name = f"{function_name} in local"


class Serverless:
    errors: list = []
    api_url = getattr(settings, "API_URL", False)
    use_local_lambda = getattr(settings, "USE_LOCAL_LAMBDA", False)

    def __init__(
            self, main_task: AsyncTask, errors=None, params: dict = None):
        # import inspect
        self.main_task = main_task
        if errors:
            self.errors = errors
        else:
            self.errors = []
        self.new_tasks = []
        self.params: dict = {}
        if params:
            self.params = params
        elif main_task.original_request:
            new_params = main_task.original_request
            self.params = new_params
        self.params["webhook_url"] = f"{self.api_url}task/webhook_aws/"
        self.is_from_aws = None
        if main_task.task_function:
            self.is_from_aws = self.main_task.task_function.is_from_aws
        if self.use_local_lambda:
            self.params["s3"] = build_s3()
        fn_name = None
        if task_function := main_task.task_function:
            fn_name = task_function.lambda_function or task_function.name
        self.function_name: Optional[str] = fn_name
        # curframe = inspect.currentframe()
        # calframe = inspect.getouterframes(curframe, 2)
        # for caller in calframe:
        #     print(caller)

    def set_function_name(self, function_name=None):
        raise NotImplementedError("set_function_name")

    def save_queue(self):
        if self.main_task.task_function.ebs_percent:
            delayed_execution(comprobate_waiting_balance, 300, force=True)
        self.main_task.status_task_id = "queue"
        self.main_task.save()
        return True

    def execute_async(self):
        # print("SE VA A EJECUTAR:", self.main_task.task_function_id)
        if not self.function_name:
            raise "DEBERÍA TENER UN NOMBRE DE FUNCIÓN"
        if self.use_local_lambda or self.is_from_aws is False:
            return self._execute_in_local()
        else:
            return self._execute_in_lambda()

    def _execute_in_lambda(self):
        from scripts.common import start_session
        s3_client, dev_resource = start_session("lambda")
        # function_name = task_function.lambda_function or task_function.name
        function_final = f"{self.function_name}:normal"
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
            errors = self.main_task.errors or []
            errors.append(error)
            self.main_task.errors = errors
            self.main_task.save()
            return False

    def _execute_in_local(self):
        import threading
        # print("FUNCTION NAME 2:", self.function_name)
        if not globals().get(self.function_name, False):
            return self._execute_in_lambda()

        # print("SE EJECUTA EN LOCAL:", function_name)
        request_id = self.main_task.id
        self.params["artificial_request_id"] = str(request_id)
        self.main_task.request_id = request_id
        self.main_task.status_task_id = "running"
        self.main_task.save()

        def run_in_thread():
            context = Context(request_id, self.function_name)
            globals()[self.function_name](self.params, context)

        t = threading.Thread(target=run_in_thread)
        t.start()
        return True


class TaskChecker:

    def __init__(self, main_task: AsyncTask = None):
        self.main_task = main_task

    def debug_all(self):
        success_executed = self.debug_success()
        print("SUCCESS EXECUTED:", success_executed)
        if not success_executed:
            sucess_queue = self.debug_queue()
            if not sucess_queue:
                self.debug_ebs()
            self.debug_ebs()
        self.debug_aged_running()

    def debug_success(self):
        from task.main_views_aws import AwsFunction

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
        # print("QUEUE TASKS:", queue_tasks.count())
        # if queue_tasks.exists():
        #     print("first task_id:", queue_tasks.first().id)
        #     print("first task:", queue_tasks.first())
        if queue_tasks.exists():
            some = False
            queue_tasks = queue_tasks.exclude(
                task_function__group_queue__isnull=False)
            print("QUEUE TASKS:", queue_tasks.count())
            self._execute_many_tasks(queue_tasks)
            next_group_task = queue_tasks.filter(
                task_function__group_queue__isnull=False).first()
            print("next_group_task:", next_group_task)
            if next_group_task:
                self.main_task = next_group_task
                group_queue = queue_tasks.filter(
                    task_function=next_group_task.task_function)
                some = self.comprobate_group_queue(group_queue)
            return queue_tasks.exists() or some

    def debug_ebs(self):
        ebs_tasks = AsyncTask.objects.in_queue(ebs=True)
        if ebs_tasks.exists():
            first_ebs = ebs_tasks.first()
            return self.comprobate_ebs(
                want_send=True, ebs_task=first_ebs, force=True)

    def debug_aged_running(self):
        from task.main_views_aws import AwsBody
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
            AwsBody(body=body)

    def find_stage(self, task):
        stage = task.task_function.stages.first()
        if stage:
            return stage.name
        if task.parent_task:
            return self.find_stage(task.parent_task)
        return None

    def comprobate_queue(self, force_ebs=False):
        task_function = self.main_task.task_function
        if not task_function.is_queueable:
            return
        if not self.main_task.status_task.is_completed:
            return

        if task_function.ebs_percent:
            self.comprobate_ebs(force=force_ebs)
            self._save_main_task()
            return

        queue_tasks = AsyncTask.objects.in_queue(task_function=task_function)
        if not queue_tasks.exists():
            queue_tasks = AsyncTask.objects.in_queue()
            if not queue_tasks.exists():
                return
        if task_function.group_queue:
            self.comprobate_group_queue(queue_tasks)
        else:
            self._execute_first(queue_tasks)
        self._save_main_task()

    def comprobate_ebs(self, want_send=False, ebs_task=None, force=False):
        if ebs_task:
            self.main_task = ebs_task

        running_rds_tasks = AsyncTask.objects\
            .filter(task_function__ebs_percent__gt=0,
                    status_task_id="running")
        if running_rds_tasks.exists():
            return False
        queue_ebs_tasks = AsyncTask.objects.in_queue(ebs=True)
        if want_send:
            queue_ebs_tasks = queue_ebs_tasks.exclude(id=self.main_task.id)
        if queue_ebs_tasks.exists() and not force:
            return False
        filter_kwargs = {}
        if self.main_task:
            filter_kwargs["task_function"] = self.main_task.task_function
        pending_rds_tasks = AsyncTask.objects.in_queue(ebs=True, **filter_kwargs)
        if want_send:
            pending_rds_tasks = pending_rds_tasks.exclude(id=self.main_task.id)
        has_pending = pending_rds_tasks.exists()
        if not has_pending:
            pending_rds_tasks = AsyncTask.objects.in_queue(ebs=True)
            if want_send:
                pending_rds_tasks = pending_rds_tasks.exclude(id=self.main_task.id)
            has_pending = pending_rds_tasks.exists()
        if has_pending or want_send:
            task_function = self.main_task.task_function
            has_balance = has_enough_balance(task_function)
            if has_balance:
                if has_pending:
                    return self._execute_first(pending_rds_tasks)
                else:
                    return self._execute_main_task()
            else:
                delayed_execution(
                    comprobate_waiting_balance, 300, main_task=self.main_task)
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
                # RICK TASK2: por qué estábamos haciendo esto?
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
