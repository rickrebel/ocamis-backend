from task.main_views_aws import AwsFunction
from respond.models import MonthRecord
from django.db.models import QuerySet
from data_param.models import Collection
from respond.models import TableFile
from typing import Any, Optional


class PreInsertMix:

    def __init__(self, month_records: QuerySet(MonthRecord),
                 base_task: AwsFunction = None):
        self.base_task = base_task
        self.month_records = month_records
        self.collection: Optional[Collection] = None
        self.collection_table_files = TableFile.objects.filter(
            lap_sheet__cat_inserted=False, lap_sheet__lap=0,
            lap_sheet__sheet_file__month_records__in=self.month_records,
            collection__app_label="med_cat", inserted=False)

    def __call__(self):

        collection_ids = self.collection_table_files.values_list(
            "collection", flat=True).distinct()
        unique_collections = set(collection_ids)
        collections = Collection.objects.filter(id__in=unique_collections)
        for collection in collections:
            self.collection = collection
            self.insert_collection()

    def insert_collection(self):
        table_files = self.collection_table_files.filter(
            collection=self.collection)


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



