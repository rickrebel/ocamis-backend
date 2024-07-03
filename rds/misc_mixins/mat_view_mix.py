from rds.models import MatView


class FromAws:

    def __init__(self, mat_view: MatView, task_params=None):
        self.mat_view = mat_view
        self.task_params = task_params

    def function_name(self, result_files):
        pass
