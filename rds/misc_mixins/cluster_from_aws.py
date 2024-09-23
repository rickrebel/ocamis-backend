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
        has_errors = child_tasks.filter(status_task__macro_status="with_errors")
        new_status = "with_errors" if has_errors else "finished"
        self.cluster.status_id = new_status
        self.cluster.save()
        return new_status

    def success_drop_base_tables(self, **kwargs):
        new_status = self.save_success_indexing()
        if new_status == "with_errors":
            return
        months_inserted = self.cluster.month_records.filter(
            stage_id="insert", status_id="finished")
        months_inserted.update(stage_id="indexing", last_insertion=None)
