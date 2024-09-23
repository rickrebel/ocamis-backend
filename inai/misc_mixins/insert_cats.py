from task.main_views_aws import AwsFunction
from respond.models import MonthRecord
from django.db.models import QuerySet
from data_param.models import Collection
from respond.models import TableFile
from typing import Any, Optional


def test_base():
    from respond.models import MonthRecord, TableFile
    month_records = MonthRecord.objects.filter(
        provider__acronym="IMSS (Ordinario)",
        year_month='2018-11')
    print("month_records", month_records.count())
    collection_table_files = TableFile.objects.filter(
        lap_sheet__cat_inserted=False, lap_sheet__lap=0,
        lap_sheet__sheet_file__month_records__in=month_records,
        provider__acronym="IMSS (Ordinario)",
        collection__app_label="med_cat")\
        .values_list("collection", flat=True).distinct()
    print("collection_table_files", collection_table_files)
    print("collection_table_files count", len(collection_table_files))
    unique_collections = set(collection_table_files.values_list(
        "collection", flat=True).distinct())
    # print("collection_table_files", collection_table_files.count())
    # collection_ids = collection_table_files.values_list(
    #     "collection", flat=True).distinct()
    # unique_collections = set(collection_ids)
    # print("unique_collections", unique_collections)
    # collections = Collection.objects.filter(id__in=unique_collections)



