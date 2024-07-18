from rds.models import MatView
from task.builder import TaskBuilder


class FromAws:

    def __init__(self, mat_view: MatView, base_task: TaskBuilder = None):
        self.mat_view = mat_view

    def function_name(self, result_files):
        pass
