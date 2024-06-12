from rds.models import ClusterYear


class FromAws:

    def __init__(self, cluster_year: ClusterYear, task_params=None):
        self.cluster_year = cluster_year
        self.task_params = task_params

    def function_name(self, result_files):
        pass
