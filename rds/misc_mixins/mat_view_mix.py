from rds.models import MatView
from task.base_views import TaskBuilder


class FromAws:

    def __init__(self, mat_view: MatView, base_task: TaskBuilder = None):
        self.mat_view = mat_view
        self.task_params = {"parent_task": base_task.main_task}

    def function_name(self, result_files):
        pass
