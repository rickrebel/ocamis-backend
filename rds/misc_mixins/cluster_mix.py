from rds.models import Cluster
from task.base_views import TaskBuilder


class FromAws:

    def __init__(self, cluster: Cluster, base_task: TaskBuilder = None):
        self.cluster = cluster
        self.base_task = base_task
        self.task_params = {"parent_task": base_task.main_task}

    def function_name(self, result_files):
        pass
