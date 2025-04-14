

def save_temp_tables_in_s3(cluster_name):
    from task.aws.query_commons import QueryExecution
    from inai.models import MonthRecord
    from scripts.common import build_s3
    from task.aws.common import BotoUtils
    from respond.models import get_month_file_name
    from inai.misc_mixins.month_record_mix import (
        MonthRecordMix, formula_tables)
    s3_base = build_s3()
    s3_utils = BotoUtils(s3_base)
    month_records = MonthRecord.objects.filter(
        stage_id='insert', status_id='finished', cluster__name=cluster_name)
    for month_record in month_records:
        print("month_record", month_record)
        month_method = MonthRecordMix(month_record)
        base_table = month_record.cluster.name
        for table_name in formula_tables:
            month_method.build_formula_table_queries(base_table, table_name)
        event = month_method.params
        # print("event", event)
        query_execution = QueryExecution(event, None)
        if export_tables_s3 := event.get("export_tables_s3", []):
            query_execution.execute_many_queries(
                export_tables_s3, need_sleep=True)
        for month_path in event.get("month_paths", []):
            s3_utils.change_storage_class(month_path, "DEEP_ARCHIVE")
        month_tables = month_record.month_table_files.all()
        # print("month_tables", month_tables)
        for month_table in month_tables:
            month_table.inserted = True
            file_name = get_month_file_name(month_table)
            month_table.file = file_name
            month_table.save()
        query_execution.execute_many_queries(event.get("drop_queries", []))
        query_execution.finish_and_save()


# save_temp_tables_in_s3('nal')


class Request:
    user = None
    def __init__(self):
        self.query_params = {}


def send_drop_base_tables(cluster_name):
    from rds.misc_mixins.cluster_mix import ClusterMix
    from inai.models import Cluster
    from task.builder import TaskBuilder
    cluster = Cluster.objects.get(name=cluster_name)
    request = Request()
    base_task = TaskBuilder(
        "revert_insert", models=[cluster], request=request)
    cluster_mix = ClusterMix(cluster, base_task)
    cluster_mix.revert_insert()


# send_drop_base_tables('issste23_24')


def clean_cluster_tables(cluster_name):
    from rds.misc_mixins.cluster_mix import ClusterMix
    from inai.models import Cluster
    from task.builder import TaskBuilder
    cluster = Cluster.objects.get(name=cluster_name)
    request = Request()
    base_task = TaskBuilder(
        "revert_insert", models=[cluster], request=request)
    cluster_mix = ClusterMix(cluster)
    cluster_mix.clean_cluster_tables()


# clean_cluster_tables('first')


def clean_cluster_tables_original(stage_name=None):
    from respond.models import TableFile
    from inai.models import Cluster
    from scripts.s3_cleaning.clean_bucket import delete_files

    cluster_name = 'first'
    cluster = Cluster.objects.get(name=cluster_name)
    table_files = TableFile.objects.filter(
        week_record__month_record__cluster=cluster,
        lap_sheet__isnull=True)
    url_paths = table_files.values_list("file", flat=True)
    url_paths = list(set(url_paths))
    # table_files.delete()
    # print("url_paths", url_paths)
    print("count", len(url_paths))
    # files_report = delete_files(url_paths)


def recover_mat_views(cluster_name):
    from rds.models import Cluster, MatView
    from formula.views import ConstraintBuilder
    from task.builder import TaskBuilder
    from django.conf import settings
    ocamis_db = getattr(settings, "DATABASES", { }).get("default")
    mat_views = MatView.objects.filter(is_active=True)
    request = Request()
    cluster = Cluster.objects.get(name=cluster_name)
    base_task = TaskBuilder(
        "revert_insert", models=[cluster], request=request)
    # from task.builder import TaskBuilder
    builder = ConstraintBuilder(
        prov_year_month=cluster.name, group='cluster', cluster=cluster)
    for mat_view in mat_views:
        # mat_view_task = TaskBuilder(
        #     'basic_mat_views_by_view', models=[self.cluster, mat_view],
        #     parent_class=self.base_task, keep_tasks=True)
        queries = builder.mat_view_queries(mat_view)
        query = queries[2]
        # print("query", query)
        if query["name"] != "copy":
            print("continue", query["name"])
            continue
        params = {
            "main_script": query["script"], "db_config": ocamis_db }
        constraint_task = TaskBuilder(
            'add_mat_view', models=[cluster, mat_view],
            parent_class=base_task,
            params=params, keep_tasks=True, subgroup=query["name"])
        constraint_task.async_in_lambda()


# recover_mat_views('imss23')


def delete_base_tables(cluster_name):
    from rds.models import Cluster, MatView
    from task.builder import TaskBuilder
    from inai.misc_mixins.month_record_mix import formula_tables
    from django.conf import settings
    cluster = Cluster.objects.get(name=cluster_name)
    drop_queries = []
    new_formula_tables = formula_tables.copy()
    # reverse formula tables
    new_formula_tables = new_formula_tables[::-1]
    request = Request()
    ocamis_db = getattr(settings, "DATABASES", {}).get("default")
    base_task = TaskBuilder(
        "revert_insert", models=[cluster], request=request)
    for table_name in new_formula_tables:
        base_table_name = f"frm_{cluster.name}_{table_name}"
        drop_queries.append(f"DROP TABLE IF EXISTS base.{base_table_name};")
    # print("drop_queries", drop_queries)
    params = {"constraint_queries": drop_queries, "db_config": ocamis_db}
    drop_task = TaskBuilder(
        'add_constraint', models=[cluster], subgroup="delete_base_tables",
        params=params, keep_tasks=True, parent_class=base_task)
    drop_task.async_in_lambda()


def change_reply_file_storage_class():
    from scripts.common import build_s3
    from task.aws.common import BotoUtils
    from respond.models import set_upload_reply_path, ReplyFile
    from respond.data_file_mixins.base_transform import get_only_path_name
    s3_base = build_s3()
    s3_utils = BotoUtils(s3_base)
    decompressed_files = ReplyFile.objects.filter(
        data_file_childs__isnull=False).distinct()
    print("decompressed_files", decompressed_files.count())
    other_files = ReplyFile.objects.filter(
        data_file_childs__isnull=True, url_download__isnull=True).distinct()
    print("other_files", other_files.count())
    def move_and_change_storage(reply_files, deep=False):
        storage_name = "DEEP_ARCHIVE" if deep else "GLACIER_IR"
        count = 0
        for reply_file in reply_files:
            full_name = reply_file.file.name
            file_name = get_only_path_name(reply_file, reply_file.petition)
            new_file_path = set_upload_reply_path(reply_file, file_name)
            if full_name == new_file_path:
                continue
            if s3_utils.check_exist(new_file_path):
                print("already exist:", new_file_path, "|", reply_file.id)
                continue
            if count % 200 == 0:
                print("count", count)
            count += 1
            # print("full_name", full_name)
            # print(" new_file", new_file_path)
            # print("-" * 10)
            # continue
            try:
                s3_utils.change_storage_class(
                    full_name, storage_name, path_destiny=new_file_path)
            except Exception as e:
                print("full_name", full_name, "|", reply_file.id)
                print(" new_file", new_file_path)
                print("error raro:\n", e)
                print("-" * 50)
            reply_file.file = new_file_path
            if deep:
                reply_file.instant_access = False
            reply_file.save()
    # move_and_change_storage(decompressed_files, deep=True)
    move_and_change_storage(other_files, deep=False)


def test_move(path_file):
    from task.aws.common import BotoUtils
    from scripts.common import build_s3
    s3_base = build_s3()
    s3_utils = BotoUtils(s3_base)
    path_destiny = path_file.replace("ssa-ags/", "ssa-ags-copy/")
    s3_utils.change_storage_class(path_file, "STANDARD", path_destiny=path_destiny)


# test_move("localhost/estatal/ssa-ags/23000425/rx_by_week_2017_18_2017_5_317_dd.csv")


from task.aws.common import BotoUtils
from scripts.common import build_s3


class TestStorage:
    s3_base = build_s3()
    s3_utils = BotoUtils(s3_base)

    def __init__(self):
        self.path_file: str = ""
        self.path_destiny: str = ""

    def test_gzip(self, path_file):
        csv_content = self.s3_utils.get_object_csv(path_file)
        for idx_row, row in enumerate(csv_content):
            print("row", idx_row, row)
            if idx_row > 10:
                break

    def test_compress(self, is_gzip=True):
        from io import StringIO
        import csv
        csv_data = StringIO()
        buffer = csv.writer(csv_data, delimiter="|")
        example_data = [
            ["ábaco", "b", "c"],
            ["ñañaras", "e", "f"],
            ["üÁÉÍÓÚ", "h", "i"]
        ]
        buffer.writerows(example_data)
        self.s3_utils.save_csv_in_aws(csv_data, self.path_file, is_gzip=is_gzip)

    def run_examples(self, examples=None):
        if not examples:
            examples = [
                ("localhost/tests/example_from_csv_file.csv", True, True),
                ("localhost/tests/example2.csv", True, False),
                ("localhost/tests/example3.csv.gz", True, False),
                ("localhost/tests/example4.csv", False, False),
                ("localhost/tests/example4.csv", True, True),
            ]

        for path_file, is_gzip, saved in examples:
            self.path_file = path_file
            self.path_destiny = self.path_file.replace(".csv", "-compressed.csv")
            print("path_file", self.path_file)
            if saved:
                self.s3_utils.move_and_gzip_file(
                    self.path_file, self.path_destiny)
                self.test_gzip(self.path_destiny)
            else:
                self.test_compress(is_gzip=is_gzip)
                self.test_gzip(path_file)
            print("-" * 50)
