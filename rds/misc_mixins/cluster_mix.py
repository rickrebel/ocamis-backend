from rds.models import Cluster
from task.base_views import TaskBuilder


class FromAws:

    def __init__(self, cluster: Cluster, task_params=None,
                 base_task: TaskBuilder = None):
        self.cluster = cluster
        self.task_params = task_params

    def function_name(self, result_files):
        pass
