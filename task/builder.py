from classify_task.models import TaskFunction
from task.helpers import TaskHelper
from task.models import AsyncTask
from task.views import camel_to_snake
from datetime import datetime


# task_built = TaskBuilder.build_special()
# task_built.build()


class TaskBuilder(TaskHelper):
    request = None

    def __init__(
            self,
            function_name: str = None,
            models: list = None,
            parent_task: AsyncTask = None,
            parent_class: TaskHelper = None,
            request=None,
            function_after: str = None,
            finished_function: str = None,
            is_massive: bool = False,
            subgroup: str = None,
            keep_tasks: bool = False,
            from_aws: bool = False,
            **kwargs
    ):
        # RICK TASK2: TODO: Revisar si se puede quitar el from_aws

        self.from_aws = from_aws
        self.expired_tasks = []
        self.main_task = AsyncTask(date_start=datetime.now())

        remain_models = []
        model_obj = None
        if models:
            model_obj = models[0]
            remain_models = models[1:]

        self.keep_tasks = keep_tasks
        self.main_task.is_massive = is_massive
        if subgroup:
            self.main_task.subgroup = subgroup
            self.main_task.is_massive = "|" in subgroup

        if parent_task:
            self.main_task.parent_task = parent_task
        elif parent_class:
            self.main_task.parent_task = parent_class.main_task

        if finished_function:
            self.main_task.finished_function = finished_function

        # self.params = {}

        if function_after:
            self.main_task.function_after = function_after
        # if params_after:
        #     self.main_task.params_after = params_after
        # else:
        #     self.main_task.params_after = {}
        # self.params_after = params_after or {}

        if self.main_task.user:
            pass
        elif self.main_task.parent_task and self.main_task.parent_task.user:
            self.main_task.user = self.main_task.parent_task.user
        elif request:
            self.main_task.user = request.user

        print("-x Function name", function_name)
        super().__init__(self.main_task, parent_class=parent_class,
                         model_obj=model_obj, **kwargs)
        self.set_function_name(function_name)
        if self.model_obj:
            self.build()
        if remain_models:
            self.set_models(remain_models)

    def set_function_name(self, function_name=None):
        from task.serverless import camel_to_snake
        if function_name:
            task_function, created = TaskFunction.objects.get_or_create(
                name=function_name)
            if created:
                model_name = camel_to_snake(self.model_obj.__class__.__name__)
                task_function.model_name = model_name
                task_function.public_name = (
                    f"{function_name} (Creada por excepción)")
                task_function.is_active = True
                task_function.save()
            # print("Task function", task_function.name)
            self.params["function_name"] = function_name
            self.main_task.task_function = task_function

    # @staticmethod
    # def build_special(clss, model_obj=None):
    #     second_object = TaskBuilder(model_obj=model_obj)
    #     second_object = clss(model_obj=model_obj)
    #     return second_object

    def build(self, model_obj=None):

        if model_obj:
            self.model_obj = model_obj

        if not self.model_obj:
            raise Exception("No se ha encontrado el modelo")

        model_name = self.set_model(self.model_obj)

        if model_name == "data_file":
            stage = self.main_task.task_function.stages.last()
            if stage:
                self.model_obj.stage = stage
                self.model_obj.status_id = "pending"
                self.model_obj.save()

        self.start_update_previous_tasks(model_name)

        self.main_task.save()
        self.add_new_task()

    def start_update_previous_tasks(self, model_name):
        filter_kwargs = {model_name: self.model_obj}
        if self.main_task.subgroup:
            filter_kwargs["subgroup"] = self.main_task.subgroup

        if not self.main_task.is_massive and not self.keep_tasks:
            previous_tasks = AsyncTask.objects.filter(**filter_kwargs)
            self.update_previous_tasks(previous_tasks)
            self.send_channel_update()

    def update_previous_tasks(self, tasks):
        to_expired_tasks = tasks.filter(is_current=True)
        if to_expired_tasks.exists():
            self.expired_tasks += to_expired_tasks
            to_expired_tasks.update(is_current=False)
        all_children = AsyncTask.objects.filter(parent_task__in=tasks)
        if all_children.exists():
            self.update_previous_tasks(all_children)
        # for task in tasks:
        #     # task.is_current = False
        #     # task.save()
        #     if task.child_tasks.filter(is_current=True).exists():
        #         self.update_previous_tasks(task.child_tasks.all())

    def send_channel_update(self):
        from task.models import send_result_to_channel
        if not self.expired_tasks:
            return
        expired_ids = [task.id for task in self.expired_tasks]
        # print("Expired tasks", expired_ids)
        result = {
            "model": "AsyncTask",
            "expired_ids": expired_ids,
            "new_task_id": self.main_task.id
        }
        send_result_to_channel(result)

    # RICK TASK2: Esto ya no me convenció nadita
    def get_child_base(self, function_name=None, **kwargs):
        if not function_name:
            function_name = self.main_task.task_function_id
        child_task = TaskBuilder(
            function_name, parent_class=self, **kwargs)
        return child_task

    def set_model(self, model):
        model_name = camel_to_snake(model.__class__.__name__)
        setattr(self.main_task, model_name, model)
        return model_name

    def set_models(self, models):
        [self.set_model(model) for model in models]
