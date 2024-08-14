from task.models import AsyncTask
from task.serverless import Serverless, TaskChecker


class HttpResponseError(Exception):
    def __init__(self, body_response, http_status=400):
        self.body_response = body_response
        self.http_status = http_status
        self.errors = body_response.get("errors", [])
        super().__init__(self.body_response)

    def send_response(self):
        from rest_framework.response import Response
        return Response(self.body_response, status=self.http_status)


class TaskHelper(Serverless):
    task_models = [
        "file_control", "reply_file", "sheet_file", "data_file",
        "week_record", "month_record", "cluster", "mat_view"]

    def __init__(self, main_task: AsyncTask, want_http_response=None,
                 parent_class=None, model_obj=None, **kwargs):
        super().__init__(main_task, **kwargs)
        self.want_http_response = want_http_response
        self.parent_class = parent_class
        self.model_obj = model_obj
        self.checker = TaskChecker(self.main_task)

    def async_in_lambda(self):
        import traceback
        task_function = self.main_task.task_function
        if not self.main_task.function_after:
            self.main_task.function_after = f"{task_function.name}_after"
        self.main_task.original_request = self.params
        self.main_task.status_task_id = "pending"

        try:
            self.main_task.save()
            # TODO Task: Corroborar que no debemos corroborar nadita
            self.comprobate_send()
        except Exception as e:
            # error = f"ERROR AL CREAR TASK: {e}, vars: {query_kwargs}"
            error_ = traceback.format_exc()
            error = f"ERROR AL CREAR TASK: {str(e)}, {self.main_task}\n{error_}"
            print(error)
            print("-" * 50)
            print(self.main_task.__dict__)
            # self.errors.append(error)
            return self.add_errors_and_raise([error])

    def comprobate_send(self):
        task_function = self.main_task.task_function
        if not task_function.is_queueable:
            self.execute_async()

        elif task_function.ebs_percent:
            self.save_queue()
            res = self.checker.comprobate_ebs(want_send=True)
            if not res:
                self.main_task.save()
        else:
            self._individual_queueable(task_function)

    def comprobate_status(
            self, want_http_response=None, explore_parent=True, force=False):

        if want_http_response is not None:
            self.want_http_response = want_http_response

        if not self.main_task:
            raise Exception("No se ha encontrado la tarea enviada")
        if self.errors and (not explore_parent or not self.parent_class):
            original_errors = self.main_task.errors or []
            original_errors.extend(self.errors)
            unique_errors = list(set(original_errors))
            self.main_task.errors = unique_errors
            new_status_task_id = "with_errors"
            if any("AWSError" in error for error in self.errors):
                new_status_task_id = "not_executed"
        # RICK TODO: Esto debemos implementarlo cuando se crean las tareas
        elif self.new_tasks:
            new_status_task_id = "children_tasks"
        else:
            new_status_task_id = "finished"
        self.save_new_status(new_status_task_id)
        # RICK TODO: No tengo claro para qué esto otra vez
        self.add_many_tasks(self.new_tasks)

        self.checker.comprobate_queue(force=force)

        if self.want_http_response is not False:
            body_response = {"new_task": self.main_task.id}
            if self.errors:
                body_response["errors"] = self.errors
                # return HttpResponse(body_response, status=400)
                raise HttpResponseError(body_response, 400)
            elif self.want_http_response:
                if self.new_tasks:
                    raise HttpResponseError(body_response, 202)
                # RICK TASK2 TODO: no estoy seguro de esto
                if explore_parent and self.parent_class and self.parent_class.new_tasks:
                    print("ESTOY EN EXPLORE_PARENT !!!!!")
                    return self.parent_class.comprobate_status(
                        want_http_response=True, explore_parent=False)
                    # return HttpResponse(body_response, status=200)

    def add_many_tasks(self, new_tasks: list, from_child=False):
        for new_task in new_tasks:
            self.add_new_task(new_task, from_child)

    def add_new_task(self, new_task=None, from_child=False):
        if from_child and new_task:
            if new_task not in self.new_tasks:
                self.new_tasks.append(new_task)
        if self.parent_class:
            if not new_task:
                new_task = self.main_task
            self.parent_class.add_new_task(new_task, from_child=True)

    def add_errors(self, errors: list = None, save=False, comprobate=True,
                   http_response=False):
        if errors:
            for new_error in errors:
                if new_error not in self.errors:
                    self.errors.append(new_error)
            if self.parent_class:
                self.parent_class.add_errors(errors)
            if save:
                self.main_task.errors = errors
        if comprobate or http_response is not False:
            self.comprobate_status(want_http_response=http_response)
        return self.errors

    def add_errors_and_raise(self, errors: list):
        self.add_errors(errors, save=True, http_response=True)

    def _comprobate_children_errors(self):
        parent_task = self.main_task.parent_task
        children_with_errors = AsyncTask.objects.filter(
            parent_task=parent_task,
            status_task__macro_status="with_errors")
        if children_with_errors.exists():
            return "some_errors"
        else:
            return "finished"

    def _run_parent_finished_function(self):
        from task.main_views_aws import AwsFunction
        from task.builder import TaskBuilder
        # print("EJECUTANDO FINISHED FUNCTION")
        parent_task = self.main_task.parent_task
        finished_function = parent_task.finished_function
        if not finished_function:
            return self._comprobate_children_errors()
        # print("FINISHED FUNCTION: ", finished_function)
        brothers_in_finish = parent_task.child_tasks.filter(
            task_function_id=finished_function)
        if brothers_in_finish.exists():
            return self._comprobate_children_errors()

        models = self._find_task_model(parent_task, many=True)
        finished_task = TaskBuilder(
            finished_function, models=models,
            parent_task=parent_task, keep_tasks=True)
        aws_function = AwsFunction(
            main_task=finished_task.main_task,
            parent_task=parent_task, function_name=finished_function)
        aws_function.execute_next_function()

    def _find_task_model(self, async_task=None, many=False):
        # "cluster", "mat_view"]
        if not async_task:
            async_task = self.main_task

        models = []
        for model in self.task_models:
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
        self._comprobate_brothers_and_finished_function()

    def _comprobate_brothers_and_finished_function(self):
        is_final = self.main_task.status_task.is_completed
        parent_task = self.main_task.parent_task
        if is_final and parent_task:
            brothers_incomplete = AsyncTask.objects.filter(
                parent_task=parent_task,
                status_task__is_completed=False)
            if brothers_incomplete.exists():
                parent_status_task_id = "children_tasks"
            else:
                parent_status_task_id = self._run_parent_finished_function()
            if parent_status_task_id:
                parent_helper = TaskHelper(parent_task)
                parent_helper.save_new_status(parent_status_task_id)

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
        group_queue = None
        if task_function.group_queue:
            # group_queue = query_kwargs.get(task_function.group_queue, False)
            group_queue = getattr(self.main_task, task_function.group_queue)
        if not group_queue:
            return self.save_queue()

        filter_group = {f"{task_function.group_queue}": group_queue}
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
