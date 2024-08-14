from rds.models import Cluster
from task.builder import TaskBuilder


class FromAws:

    def __init__(self, cluster: Cluster, base_task: TaskBuilder = None):
        self.cluster = cluster
        self.base_task = base_task

    def add_constraint_after(self, **kwargs):
        pass

    def add_mat_view_after(self, **kwargs):
        pass

    def save_success_indexing(self, **kwargs):
        child_tasks = self.base_task.main_task.child_tasks.all()
        if not child_tasks.filter(status_task__macro_status="with_errors"):
            self.cluster.status_id = "finished"
            self.cluster.save()
        else:
            self.cluster.status_id = "with_errors"
            self.cluster.save()
