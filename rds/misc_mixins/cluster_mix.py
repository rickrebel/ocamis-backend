from rds.models import Cluster, MatView
from task.builder import TaskBuilder
from django.conf import settings
from formula.views import ConstraintBuilder
ocamis_db = getattr(settings, "DATABASES", {}).get("default")


class ClusterMix:

    def __init__(self, cluster: Cluster, base_task: TaskBuilder = None):
        self.cluster = cluster
        self.base_task = base_task
        self.builder = ConstraintBuilder(
            prov_year_month=cluster.name, group='cluster', cluster=cluster)

    def revert_cluster_stages(self, **kwargs):
        self.builder.is_create = False

        self.create_basic_mat_views1(is_create=False)
        constraints = self.builder.modify_constraints()
        all_constraints = [constraint for (constraint, _) in constraints]
        params = {"constraint_queries": all_constraints, "db_config": ocamis_db}
        constraint_task = TaskBuilder(
            'add_constraint', models=[self.cluster], subgroup="revert",
            parent_class=self.base_task, params=params, keep_tasks=True)
        constraint_task.async_in_lambda()

    def indexing_cluster(self, **kwargs):
        # print("indexing_cluster")
        constraints = self.builder.modify_constraints()
        for (constraint, operation) in constraints:
            # print("constraint:\n", constraint, "\n")
            params = {"constraint": constraint, "db_config": ocamis_db}
            constraint_task = TaskBuilder(
                'add_constraint', models=[self.cluster, operation],
                parent_class=self.base_task, params=params, keep_tasks=True)
            constraint_task.async_in_lambda()

    def create_basic_mat_views1(self, **kwargs):
        stage_name = kwargs.get("stage_name", "basic_mat_views_1")
        is_create = kwargs.get("is_create", True)
        mat_views = MatView.objects.filter(is_active=True)
        if is_create:
            mat_views = mat_views.filter(stage_belongs_id=stage_name)
        for mat_view in mat_views:
            mat_view_task = TaskBuilder(
                'basic_mat_views_by_view', models=[self.cluster, mat_view],
                parent_class=self.base_task, keep_tasks=True)
            queries = self.builder.mat_view_queries(mat_view)
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
