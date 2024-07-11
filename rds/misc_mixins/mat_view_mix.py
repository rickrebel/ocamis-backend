from rds.models import MatView
from task.base_views import TaskBuilder


class FromAws:

    def __init__(self, mat_view: MatView, task_params=None,
                 base_task: TaskBuilder = None):
        self.mat_view = mat_view
        self.task_params = task_params

    def function_name(self, result_files):
        pass
