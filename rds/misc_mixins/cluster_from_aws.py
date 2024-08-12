from rds.models import Cluster
from task.builder import TaskBuilder


class FromAws:

    def __init__(self, cluster: Cluster, base_task: TaskBuilder = None):
        self.cluster = cluster
        self.base_task = base_task

    def add_constraint_after(self, **kwargs):
        pass
