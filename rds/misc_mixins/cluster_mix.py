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
                parent_class=self.base_task, params=params, keep_tasks=True)
            constraint_task.async_in_lambda()

    def create_basic_mat_views1(self, **kwargs):
        from formula.views import ConstraintBuilder
        from rds.models import MatView
        print("indexing_cluster")
        mat_views = MatView.objects.filter(
            is_active=True, stage_belongs_id='basic_mat_views_1')
        builder = ConstraintBuilder(
            prov_year_month=self.cluster.name, group='cluster',
            cluster=self.cluster)
        for mat_view in mat_views:
            mat_view_task = TaskBuilder(
                'basic_mat_views_by_view', models=[self.cluster, mat_view],
                parent_class=self.base_task, keep_tasks=True)
            queries = builder.mat_view_queries(mat_view)
            for query in queries:
                params = {
                    "main_script": query["script"], "db_config": ocamis_db}
                constraint_task = TaskBuilder(
                    'add_mat_view', models=[self.cluster, mat_view],
                    parent_class=mat_view_task, params=params,
                    keep_tasks=True, subgroup=query["name"])
                constraint_task.async_in_lambda()


def my_test():
    from formula.views import ConstraintBuilder
    base_table = 'test1'
    builder = ConstraintBuilder(prov_year_month=base_table, group='cluster')
    constraints = builder.modify_constraints()
    for (constraint, operation) in constraints:
        print("-" * 50)
        print(constraint)
    print(constraints)
