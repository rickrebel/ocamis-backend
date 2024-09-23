import gzip
import shutil
# import os
from django.conf import settings

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def csv_to_gz(csv_filepath, gz_filepath):
    try:
        with open(csv_filepath, 'rb') as f_in:
            with gzip.open(gz_filepath, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    except Exception as e:
        print(e)


def transform_gz(file_name):
    base_dir = settings.BASE_DIR
    origin_path = f"{base_dir}\\fixture\\gz_files\\{file_name}"
    final_path = f"{base_dir}\\fixture\\gz_files\\{file_name}.gz"

    csv_to_gz(origin_path, final_path)


def simple_example():
    # transform_gz("2017_chih.txt")
    transform_gz("Jalisco.csv")

# february_files = [
#     "Febrero 2022-Chihuahua.xlsx",
#     "Febrero 2022-Coahuila.xlsx",
#     "Febrero 2022-Baja California Norte.xlsx",
# ]

# january_files = [
#     "Enero 2022-Chihuahua.xlsx",
#     "Enero 2022-Coahuila.xlsx",
#     "Enero 2022-Guanajuato.xlsx",
#     "Enero 2022-Jalisco.xlsx",
#     "Enero 2022-Nuevo Leon.xlsx",
#     "Enero 2022-Sinaloa.xlsx",
#     "Enero 2022-DF Norte.xlsx",
#     "Enero 2022-DF Sur.xlsx",
#     "Enero 2022-Mexico Oriente.xlsx",
#     "Enero 2022-Mexico Poniente.xlsx",
# ]
#
# for file_name in january_files:
#     simple_name = file_name.split(".")[0]
#     for x in range(1, 4):
#         print(x)
#         csv_name = f"{simple_name}_Hoja_{x}.csv"
#         transform_gz(csv_name)


def process_regions():
    regions = [
        'Norte.xlsx',
        'Occidente.xlsx',
        'Centro.xlsx',
        'Sur.xlsx'
    ]
    for region in regions:
        for x in range(1, 7):
            print(x)
            simple_name = region.split(".")[0]
            csv_name = f"{simple_name}_{simple_name}_{x}.csv"
            transform_gz(csv_name)
            csv_name2 = f"{simple_name}_{simple_name}_{x} (2).csv"
            transform_gz(csv_name2)


# mat_views/big_example_202301_drug.csv
# mat_views/small_example_202301_drug.csv
# SELECT aws_s3.query_export_to_s3(
# 	'SELECT * FROM tmp.fm_1_202301_drug',
#     aws_commons.create_s3_uri('cdn-desabasto', 'data_files/month_tables/small_example_202301_drug.csv', 'us-west-2'),
#     options := 'format csv, delimiter "|", header true'
# );

# SELECT aws_s3.table_import_from_s3(
# 	'base.exp_drug',
# 	'uuid, prescribed_amount, delivered_amount, row_seq, rx_id, sheet_file_id, delivered_id, medicament_id, lap_sheet_id, week_record_id',
# 	'(format csv, header true, delimiter "|", encoding "UTF8")',
# 	'cdn-desabasto',
# 	'data_files/mat_views/big_example_202301_drug.csv',
# 	'us-west-2',
# 	'AKIAICSGL3ROH3GVALGQ',
# 	'fFq7NwQyj/FmdtK/weXRwgrlEArkOatITD/mJYzL'
# );

# -- CREATE TABLE base.exp_drug
# -- (LIKE public.formula_drug INCLUDING CONSTRAINTS);

# SELECT column_name
#   FROM information_schema.columns
#  WHERE table_schema = 'public'
#    AND table_name   = 'formula_drug'
# ORDER BY ordinal_position;
#
# from task.aws.common import BotoUtils
# from scripts.common import build_s3
#
# s3_base = build_s3()
# s3 = BotoUtils(s3_base)
# s3.change_storage_class("month_tables/small_example_202306_drug.csv", "DEEP_ARCHIVE")


def save_and_change_storage_class(mont_record_id=None):
    from task.aws.query_commons import QueryExecution
    from inai.models import MonthRecord
    from scripts.common import build_s3
    from task.aws.common import BotoUtils
    from inai.misc_mixins.month_record_mix import (
        MonthRecordMix, formula_tables)

    s3_base = build_s3()
    s3_utils = BotoUtils(s3_base)
    if mont_record_id:
        month_records = MonthRecord.objects.filter(id=mont_record_id)
    else:
        month_records = MonthRecord.objects.filter(
            stage_id='insert', status_id='finished')
    for month_record in month_records:
        month_method = MonthRecordMix(month_record)
        base_table = month_record.cluster.name
        for table_name in formula_tables:
            month_method.build_formula_table_queries(base_table, table_name)

        event = month_method.params
        query_execution = QueryExecution(event, None)
        if export_tables_s3 := event.get("export_tables_s3", []):
            query_execution.execute_many_queries(
                export_tables_s3, need_sleep=True)

        for month_path in event.get("month_paths", []):
            s3_utils.change_storage_class(month_path, "DEEP-ARCHIVE")


