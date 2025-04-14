
def experiment_export_with_lucian(table_name, file_path):
    from django.db import connection
    query = f"""
    SELECT aws_s3.query_export_to_s3(
        'SELECT * FROM {table_name}',
        aws_commons.create_s3_uri('cdn-desabasto', '{file_path}', 'us-west-2'),
        options := 'format csv, delimiter ''|'', header true'
    );
    """
    cursor = connection.cursor()
    cursor.execute(query)
    cursor.close()


# experiment_export_with_lucian("django_migrations", "query_export_to_s3/yeeko/django_migrations2.csv")
experiment_export_with_lucian(
    "base.frm_test1_mat_drug_totals2",
    "data_files/mat_views/test_cluster/frm_test1_mat_drug_totals2.csv")


def test_save_from_mat_view(model_in_db, headers, path=None):
    from django.db import connection
    from inai.misc_mixins.insert_month_mix import build_copy_sql_aws
    sql_copy = build_copy_sql_aws(path, model_in_db, headers)
    cursor = connection.cursor()
    cursor.execute(sql_copy)
    cursor.close()
    connection.close()


def send_test():
    my_headers = "uuid,cluster_id,delegation_id,week_record_id,delivered_id,prescribed_total,delivered_total,total"
    # table_name = "public.frm_test1_mat_drug_totals2"
    table_name = "public.mat_drug_totals2"
    final_path = "mat_views/test_cluster/frm_test1_mat_drug_totals2.csv"
    test_save_from_mat_view(table_name, my_headers, final_path)


def save_mat_view_in_db(model_name, model_in_db):
    from django.db import connection
    from respond.data_file_mixins.matches_mix import field_of_models
    from inai.misc_mixins.insert_month_mix import build_copy_sql_aws
    columns = field_of_models({"model": model_name, "app": "formula"})
    # column_names = [column["name"].replace("_total", "") for column in columns]
    column_names = [column["name"] for column in columns]
    columns_join = ",".join(column_names)
    final_path = f"mat_views/{model_in_db}.csv"
    sql_copy = build_copy_sql_aws(final_path, model_in_db, columns_join)
    cursor = connection.cursor()
    cursor.execute(sql_copy)
    cursor.close()
    connection.close()


def copy_export_sql_aws(path, model_in_db, columns_join, query):
    from django.conf import settings
    ocamis_db = getattr(settings, "DATABASES", {}).get("default")
    bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
    aws_location = getattr(settings, "AWS_LOCATION")
    region_name = getattr(settings, "AWS_S3_REGION_NAME")
    access_key = getattr(settings, "AWS_ACCESS_KEY_ID")
    secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
    return f"""
        SELECT aws_s3.query_export_to_s3(
            '{query}',
            '{columns_join}',
            '(format csv, header true, delimiter "|", encoding "UTF8")',
            '{bucket_name}',
            '{aws_location}/{path}',
            '{region_name}',
            '{access_key}',
            '{secret_key}'
        )
    """


def backup_materialized_view(materialized_view_name):
    from django.db import connection
    from datetime import datetime
    cursor = connection.cursor()
    query = f"SELECT * FROM {materialized_view_name}"
    cursor.execute(query)
    all_data = cursor.fetchall()
    print("all_data", all_data)
    print("end", datetime.now())
    cursor.close()
    connection.close()


# from django.conf import settings
# from django.db import connection
# from datetime import datetime
# materialized_view_name = "med_cat_delivered"
# bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
# cursor = connection.cursor()
# # query = f"SELECT aws_commons.create_s3_uri('{bucket_name}', 'cat_images/ejemplo.csv')"
#
# query = f"""
#     SELECT * from aws_s3.query_export_to_s3(
#         'SELECT * FROM med_cat_delivered',
#         'cdn-desabasto',
#         'cat_images/ejemplo4.csv'
#     )
# """
# cursor.execute(query)
# all_data = cursor.fetchall()
# print("all_data", all_data)
# print("end", datetime.now())
# cursor.close()
# connection.close()


def insert_id_to_csv(snake_name):
    from scripts.common import build_s3
    # from task.serverless import async_in_lambda
    from task.builder import TaskBuilder
    prev_path = "mat_views"
    params = {
        "final_path": f"{prev_path}/mother_{snake_name}.csv",
        "result_path": f"{prev_path}/mat_{snake_name}.csv",
        "s3": build_s3(),
        "is_enumerate": True
    }
    # RICK FUTURE: Esto se deberá actualizar cuando se agregue mat_views
    # insert_task = TaskBuilder("rebuild_week_csv", params=params, models=[])
    insert_task = TaskBuilder("rebuilt_csv", params=params, models=[])
    insert_task.async_in_lambda()


def sent_mat_view_to_table(model_name, build_id=False):
    from task.serverless import camel_to_snake
    snake_simple_name = camel_to_snake(model_name)
    final_model_name = f"Mat{model_name}"
    # save_mat_view_in_db("MatDrugTotals", "mat_drug_totals")
    if build_id:
        insert_id_to_csv(snake_simple_name)
    else:
        save_mat_view_in_db(final_model_name, f"mat_{snake_simple_name}")


# sent_mat_view_to_table("DrugEntity", build_id=False)

