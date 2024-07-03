from rds.models import Cluster


class FromAws:

    def __init__(self, cluster: Cluster, task_params=None):
        self.cluster = cluster
        self.task_params = task_params

    def function_name(self, result_files):
        pass
