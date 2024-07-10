from classify_task.models import TaskFunction
from task.helpers import TaskHelper
from task.models import AsyncTask
from task.views import camel_to_snake
from datetime import datetime


class TaskParams(TaskHelper):

    def __init__(
            self, function_name=None, model_obj=None, main_task=None,
            request=None, parent_task=None, finished_function=None,
            keep_tasks=False, parent_class=None, subgroup=None,
            function_after=None, params_after=None, models=None, **kwargs):

        if main_task:
            self.main_task = main_task
        else:
            self.main_task = AsyncTask(date_start=datetime.now())

        if self.main_task.pk and model_obj:
            raise Exception("No se puede crear una nueva tarea con un modelo")

        self.model_obj = model_obj

        self.keep_tasks = keep_tasks
        if subgroup:
            self.main_task.subgroup = subgroup
            self.main_task.is_massive = "|" in subgroup

        if parent_task:
            self.main_task.parent_task = parent_task
        if parent_class and not parent_task:
            self.main_task.parent_task = parent_class.main_task

        if finished_function:
            self.main_task.finished_function = finished_function

        # self.params = {}

        if function_after:
            self.main_task.function_after = function_after
        if params_after:
            self.main_task.params_after = params_after
        self.params_after = params_after or {}

        user = None
        if self.main_task.user:
            pass
        elif self.main_task.parent_task and self.main_task.parent_task.user:
            user = self.main_task.parent_task.user
        elif request:
            user = request.user
        if user:
            self.main_task.user = user

        print("Function name", function_name)
        kwargs["model_obj"] = model_obj
        super().__init__(self.main_task, parent_class=parent_class, **kwargs)
        self.set_function_name(function_name)
        if model_obj:
            self.build()
        if models:
            self.set_models(models)

    def set_function_name(self, function_name=None):
        if function_name:
            task_function, created = TaskFunction.objects.get_or_create(
                name=function_name)
            if created:
                task_function.public_name = (
                    f"{function_name} (Creada por excepción)")
                task_function.save()
            print("Task function", task_function.name)
            self.params["function_name"] = function_name
            self.main_task.task_function = task_function

    def build(self, model_obj=None):

        if model_obj:
            self.model_obj = model_obj

        if not self.model_obj:
            raise Exception("No se ha encontrado el modelo")

        model_name = camel_to_snake(self.model_obj.__class__.__name__)
        setattr(self.main_task, model_name, model_obj)

        if model_name == "data_file":
            stage = self.main_task.task_function.stages.last()
            if stage:
                self.model_obj.stage = stage
                self.model_obj.status_id = "pending"
                self.model_obj.save()

        self.start_update_previous_tasks(model_name)

        self.main_task.save()
        # self.add_new_task()

    def start_update_previous_tasks(self, model_name):
        filter_kwargs = {model_name: self.model_obj}
        if self.main_task.subgroup:
            filter_kwargs["subgroup"] = self.main_task.subgroup

        # self.create_kwargs[model_name] = model_obj
        if not self.main_task.is_massive and not self.keep_tasks:
            previous_tasks = AsyncTask.objects.filter(**filter_kwargs)
            self.update_previous_tasks(previous_tasks)

    def update_previous_tasks(self, tasks):
        tasks = tasks.filter(is_current=True)
        for task in tasks:
            task.is_current = False
            task.save()
            if task.child_tasks.filter(is_current=True).exists():
                self.update_previous_tasks(task.child_tasks.all())

    def get_child_base(self, **kwargs):
        task_params = TaskParams(
            function_name=self.main_task.task_function_id,
            parent_class=self, **kwargs)
        return task_params

    def set_models(self, models):
        for model in models:
            model_name = camel_to_snake(model.__class__.__name__)
            setattr(self.main_task, model_name, model)
