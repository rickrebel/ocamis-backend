from task.models import AsyncTask
from task.serverless import Serverless
from task.rds_balance import (
    has_enough_balance, delayed_execution, comprobate_waiting_balance)


class HttpResponseError(Exception):
    def __init__(self, body_response, http_status=400):
        self.body_response = body_response
        self.http_status = http_status
        super().__init__(self.body_response)


class TaskHelper(Serverless):

    def async_in_lambda(self, function_name=None, comprobate=True):
        self.set_function_name(function_name)
        task_function = self.main_task.task_function
        if not self.main_task.function_after:
            self.main_task.function_after = f"{task_function.name}_after"
        # self.main_task.task_function = task_function
        self.main_task.original_request = self.params
        self.main_task.status_task_id = "pending"

        try:
            self.main_task.save()
        except Exception as e:
            # error = f"ERROR AL CREAR TASK: {e}, vars: {query_kwargs}"
            error = f"ERROR AL CREAR TASK: {e}, {self.main_task}"
            print(error)
            self.errors.append(error)
            return None

        if not task_function.is_queueable:
            self.execute_async()

        elif task_function.ebs_percent:
            self.save_queue()
            res = self._comprobate_ebs(True)
            if not res:
                self.main_task.save()
        else:
            self._individual_queueable(task_function)
        if comprobate:
            return self.comprobate_status(want_http_response=False)

    def comprobate_status(self, want_http_response=None):
        if want_http_response is not None:
            self.want_http_response = want_http_response

        if not self.main_task:
            self.errors.append("No se ha encontrado la tarea enviada")
            return
        if self.errors:
            original_errors = self.main_task.errors or []
            original_errors.extend(self.errors)
            self.main_task.errors = original_errors
            new_status_task_id = "with_errors"
            for error in self.errors:
                if "AWSError" in error:
                    new_status_task_id = "not_executed"
                    break
        elif self.new_tasks:
            new_status_task_id = "children_tasks"
        else:
            new_status_task_id = "finished"
        self.save_new_status(new_status_task_id)
        self._comprobate_queue()
        self.add_new_task()
        if self.want_http_response is not False:
            body_response = {"new_task": self.main_task.id}
            if self.errors:
                body_response["errors"] = self.errors
                # return HttpResponse(body_response, status=400)
                raise HttpResponseError(body_response, 400)
            elif self.want_http_response:
                if self.new_tasks:
                    raise HttpResponseError(body_response, 202)
                    # return HttpResponse(body_response, status=200)
                else:
                    return None
        return self.main_task

    def add_many_tasks(self, new_tasks: list, from_child=False):
        for new_task in new_tasks:
            self.add_new_task(new_task, from_child)

    def add_new_task(self, new_task=None, from_child=False):
        if from_child and new_task:
            self.new_tasks.append(new_task)
        if self.parent_class:
            if not new_task:
                new_task = self.main_task
            self.parent_class.add_new_task(new_task, from_child=True)

    def add_errors(self, errors: list, save=False, comprobate=True,
                   http_response=False):
        self.errors.extend(errors)
        if self.parent_class:
            self.parent_class.add_errors(errors)
        if save:
            self.main_task.errors = errors
        if comprobate or http_response is not False:
            self.comprobate_status(want_http_response=http_response)
        return self.errors

    def _comprobate_brothers_with_errors(self):
        children_with_errors = AsyncTask.objects.filter(
            parent_task=self.main_task.parent_task,
            status_task__macro_status="with_errors")
        if children_with_errors.exists():
            return "some_errors"
        else:
            return "finished"

    def _execute_finished_function(self):
        from task.views_aws import AwsFunction
        from task.base_views import TaskBuilder
        # print("EJECUTANDO FINISHED FUNCTION")
        parent_task = self.main_task.parent_task
        finished_function = parent_task.finished_function
        if not parent_task.finished_function:
            return self._comprobate_brothers_with_errors()
        # print("FINISHED FUNCTION: ", finished_function)
        brothers_in_finish = parent_task.child_tasks.filter(
            task_function_id=finished_function)
        if brothers_in_finish.exists():
            return self._comprobate_brothers_with_errors()

        # add_elems = {"parent_task": parent_task, "keep_tasks": True}
        models = self._find_task_model(parent_task, many=True)
        # new_task, task_params = build_task_params(
        #     self.model_obj, finished_function, **add_elems)
        finished_task = TaskBuilder(
            function_name=finished_function, models=models,
            parent_task=parent_task, keep_tasks=True)
        aws_function = AwsFunction(
            main_task=finished_task.main_task,
            parent_task=parent_task, function_name=finished_function)
        new_task2 = aws_function.execute_function()
        if new_task2.status_task.is_completed:
            return self._comprobate_brothers_with_errors()
        else:
            return "children_tasks"

    def _find_task_model(self, async_task=None, many=False):
        task_models = [
            "petition", "file_control", "reply_file", "sheet_file",
            "data_file", "week_record", "month_record"]
        # "cluster", "mat_view"]
        if not async_task:
            async_task = self.main_task

        models = []
        for model in task_models:
            current_obj = getattr(async_task, model)
            if current_obj:
                if not many:
                    return current_obj
                models.append(current_obj)
        return models

    def save_new_status(self, status_task_id):
        try:
            self.main_task = self.main_task.save_status(status_task_id)
        except Exception as e:
            error = (f"ERROR AL GUARDAR NUEVO STATUS, tarea: "
                     f"{self.main_task.id}, error: {e}")
            self.errors.append(error)
        self._comprobate_brothers()

    def _comprobate_brothers(self):
        is_final = self.main_task.status_task.is_completed
        parent_task = self.main_task.parent_task
        if is_final and parent_task:
            brothers_incomplete = AsyncTask.objects.filter(
                parent_task=parent_task,
                status_task__is_completed=False)
            if brothers_incomplete.exists():
                parent_status_task_id = "children_tasks"
            else:
                parent_status_task_id = self._execute_finished_function()
            parent_helper = TaskHelper(parent_task)
            parent_helper.save_new_status(parent_status_task_id)

    def _comprobate_queue(self, is_main=False):
        task_function = self.main_task.task_function
        if not task_function.is_queueable:
            return
        if not self.main_task.status_task.is_completed:
            return

        if task_function.ebs_percent:
            self._comprobate_ebs()
        queue_tasks = AsyncTask.objects.filter(
            task_function=task_function,
            status_task_id="queue").order_by("id")
        if not queue_tasks.exists():
            return
        if task_function.group_queue:
            self._comprobate_group_queue(queue_tasks)
        else:
            self._execute_many_tasks(queue_tasks[:task_function.queue_size])
        self.main_task.save()

    def _comprobate_ebs(self, want_send=False):
        task_function = self.main_task.task_function
        rds_tasks = AsyncTask.objects.filter(task_function__ebs_percent__gt=0)
        running_rds_tasks = rds_tasks.filter(status_task_id="running")
        if running_rds_tasks.exists():
            return False
        pending_rds_tasks = rds_tasks.filter(status_task_id="queue")
        if want_send:
            pending_rds_tasks = pending_rds_tasks.exclude(id=self.main_task.id)
        has_pending = pending_rds_tasks.exists()
        if has_pending or want_send:
            has_balance = has_enough_balance(task_function)
            if has_balance:
                if has_pending:
                    return self._execute_first(pending_rds_tasks)
                else:
                    return self.execute_async()
            else:
                delayed_execution(comprobate_waiting_balance, 300)
                return False

    def _comprobate_group_queue(self, queue_tasks):
        task_function = self.main_task.task_function
        group_obj = getattr(self.main_task, task_function.group_queue)

        filter_group = {f"{task_function.group_queue}": group_obj}
        same_group_tasks = queue_tasks.filter(**filter_group)
        if same_group_tasks.exists():
            if task_function.queue_size == 1:
                return self._execute_first(same_group_tasks)
            filter_group["task_function"] = task_function
            filter_group["status_task_id"] = "running"
            running_tasks = AsyncTask.objects.filter(**filter_group)
            remain_tasks = task_function.queue_size - running_tasks.count()
            if remain_tasks > 0:
                self._execute_many_tasks(same_group_tasks[:remain_tasks])
        else:
            not_started_tasks = queue_tasks.filter(
                parent_task__status_task_id="created")
            if not not_started_tasks.exists():
                not_started_tasks = queue_tasks.filter(
                    parent_task__parent_task__status_task_id="created")
            if not_started_tasks.exists():
                self._execute_first(not_started_tasks)
                # first_task = not_started_tasks.first()
                # execute_async(first_task, first_task.original_request)
                # RICK TASK: por qué estamos haciendo esto?
                # first_task_helper = TaskHelper(first_task)
                # first_task_helper.comprobate_queue()

    def _individual_queueable(self, task_function):
        pending_tasks = AsyncTask.objects \
            .filter(
                task_function__is_queueable=True,
                status_task__is_completed=False,
                task_function=task_function) \
            .exclude(id=self.main_task.id)
        has_pending = pending_tasks.count() > 0
        if not has_pending:
            return self.execute_async()
        if task_function.simultaneous_groups == 1 and has_pending:
            return self.save_queue()
        group_obj = None
        if task_function.group_queue:
            # group_obj = query_kwargs.get(task_function.group_queue, False)
            group_obj = getattr(self.main_task, task_function.group_queue)
        if not group_obj:
            return self.save_queue()

        filter_group = {f"{task_function.group_queue}": group_obj}
        group_tasks = pending_tasks.filter(**filter_group)
        many_same_group = group_tasks.count() >= task_function.queue_size
        if many_same_group:
            return self.save_queue()
        if group_tasks.count() > 0:
            return self.execute_async()

        if task_function.simultaneous_groups > 1:
            groups_count = pending_tasks \
                .values(task_function.group_queue) \
                .distinct() \
                .count()
            many_groups = groups_count >= task_function.simultaneous_groups
            if not many_groups:
                return self.execute_async()
        return self.save_queue()

    def _execute_many_tasks(self, tasks):
        self.main_task.save()
        for task in tasks:
            next_serverless = Serverless(task)
            next_serverless.execute_async()
        return True

    def _execute_first(self, tasks):
        self.main_task.save()
        if first_task := tasks.first():
            next_serverless = Serverless(first_task)
            next_serverless.execute_async()
        return True

