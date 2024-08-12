from rds.models import Cluster
from task.builder import TaskBuilder
from django.conf import settings
ocamis_db = getattr(settings, "DATABASES", {}).get("default")


class ClusterMix:

    def __init__(self, cluster: Cluster, base_task: TaskBuilder = None):
        self.cluster = cluster
        self.base_task = base_task

    def indexing_cluster(self, **kwargs):
        from formula.views import ConstraintBuilder
        print("indexing_cluster")
        base_table = self.cluster.name
        builder = ConstraintBuilder(prov_year_month=base_table, group='cluster')
        constraints = builder.modify_constraints()
        for (constraint, operation) in constraints:
            # print("constraint:\n", constraint, "\n")
            params = {"constraint": constraint, "db_config": ocamis_db}
            constraint_task = TaskBuilder(
                'add_constraint', models=[self.cluster, operation],
                parent_class=self.base_task, params=params)
            constraint_task.async_in_lambda()


# def my_test():
#     from formula.views import ConstraintBuilder
#     base_table = 'test1'
#     builder = ConstraintBuilder(prov_year_month=base_table, group='cluster')
#     constraints = builder.modify_constraints()
#     print(constraints)

