from rds.models import Cluster
from task.builder import TaskBuilder


class FromAws:

    def __init__(self, cluster: Cluster, base_task: TaskBuilder = None):
        self.cluster = cluster
        self.base_task = base_task

    def function_name(self, result_files):
        pass
