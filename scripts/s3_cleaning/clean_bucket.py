
import csv
from datetime import datetime
from typing import Any, Dict, List

from django.conf import settings
from respond.models import TableFile
from respond.models import SheetFile
from respond.models import DataFile
from respond.models import ReplyFile


class CleanBucket:
    my_bucket: Any
    files_models_in_db: Dict[str, List] = {}
    files_in_s3: List = []
    files_in_db: List = []
    dict_files_in_db: Dict[str, int] = {}
    orphans: List = []
    responses: List = []
    in_s3_by_csv: bool = False
    global_aws_location = f"{getattr(settings, 'AWS_LOCATION', '')}/"

    def __init__(
            self, aws_location="", limit=10000, exclude_recent=False,
            run=True, only_imss=False, in_s3_by_csv=True):
        import boto3
        from django.conf import settings
        from scripts.common import build_s3
        from task.aws.common import BotoUtils

        bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
        aws_access_key_id = getattr(settings, "AWS_ACCESS_KEY_ID")
        aws_secret_access_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
        s3 = boto3.resource(
            's3', aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key)
        self.my_bucket = s3.Bucket(bucket_name)
        if "data_files/" in aws_location:
            self.aws_location = aws_location
        # else:
        #     self.aws_location = "data_files/"
        # self.aws_location = aws_location or self.aws_location
        self.excluded_dirs = [
            "admin/", "aws_errors/", "cat_images/", "catalogs/", "ckeditor/",
            "data_samples/", "experiment/", "image_rx/", "logos/",
            "mat_views/", "profile_images/", "rest_framework/",
            "sheet_samples/", "catalog/", "localhost/",]
        recent_dirs = [
            "month_tables/", "reply/", "data/", "sheet/", "table/",
            "merged_tables/",]
        self.include_dirs = []
        if not exclude_recent:
            self.excluded_dirs += recent_dirs
            if not self.aws_location:
                self.include_dirs = ["nacional/", "estatal/", "hospital/"]
        self.s3_utils = BotoUtils(build_s3())
        self.storage_name = "GLACIER_IR"
        self.run = run
        self.only_imss = only_imss
        self.report = {
            "new_data_files": 0,
            "new_sheet_files": 0,
            "already_exist": 0,
            "clone_saved": 0,
        }
        self.in_s3_by_csv = in_s3_by_csv

    def __call__(self):
        self.get_files_in_db()
        self.get_files_in_s3()
        self.find_orphans()
        print("Orphans found: ", datetime.now().strftime("%H:%M:%S"))
        self.report_orphans()

    def get_files_in_db(self):
        print("Getting files in db: ", datetime.now().strftime("%H:%M:%S"))
        model_files = [TableFile, SheetFile, DataFile, ReplyFile]
        for model in model_files:
            self.get_files_in_model(model)
        # self.files_in_db = list(set(self.files_in_db))
        for file in self.files_in_db:
            self.dict_files_in_db.setdefault(file, 0)
            self.dict_files_in_db[file] += 1

    def get_files_in_model(self, model):
        model_file_query = model.objects.filter(file__isnull=False)
        model_count = model_file_query.count()
        for i in range(0, model_count, 1000):
            self.files_in_db.extend(
                model_file_query.values_list('file', flat=True)[i:i+1000])

    def _get_s3_with_list_objects(self):
        if self.include_dirs:
            all_bucket_files = []
            for included_dir in self.include_dirs:
                all_bucket_files += self.my_bucket.objects.filter(
                    Prefix=f"{self.global_aws_location}{included_dir}")
        else:
            all_bucket_files = self.my_bucket.objects.filter(
                Prefix=self.aws_location)

        for bucket_obj in all_bucket_files:
            bucket_obj_key = bucket_obj.key.replace(
                self.global_aws_location, '')
            if any(
                    bucket_obj_key.startswith(excluded_dir)
                    for excluded_dir in self.excluded_dirs
            ):
                continue
            self.files_in_s3.append((bucket_obj_key, bucket_obj.size))

    def get_files_in_s3(self):
        from urllib.parse import unquote
        self.files_in_s3 = []

        print("Getting files in s3: ", datetime.now().strftime("%H:%M:%S"))

        if not self.in_s3_by_csv:
            return self._get_s3_with_list_objects()

        # backups/cdn-desabasto/inventory_ocamis/data/
        csv_file_path = getattr(settings, "FILES_IN_S3_CSV_FILE_PATH")
        try:
            with open(csv_file_path, mode='r') as file:
                reader = csv.reader(file)
                # data_files/estatal/ichihs/080140423000144/2%20Surtido.xlsx_SHEET_Sheet%201.csv
                lines = [row for row in reader]
        except FileNotFoundError:
            print("No se encontro el archivo csv")
            return

        for line in lines:
            line_count = len(line)
            bucket_obj_key = line[1] if line_count > 1 else ""
            bucket_obj_size = line[2] if line_count > 2 else 0
            bucket_obj_key = unquote(bucket_obj_key)
            if not bucket_obj_key or not isinstance(bucket_obj_key, str):
                continue

            bucket_obj_key = bucket_obj_key.replace(self.global_aws_location, '')

            if any(
                bucket_obj_key.startswith(excluded_dir)
                for excluded_dir in self.excluded_dirs
            ):
                continue

            self.files_in_s3.append((bucket_obj_key, bucket_obj_size))

    def find_orphans(self):
        print("Finding orphans: ", datetime.now().strftime("%H:%M:%S"))
        files_in_db = set(self.files_in_db)
        self.orphans = [
            (file, size) for file, size in self.files_in_s3 if file not in files_in_db
        ]

    def report_orphans(self):
        total_size = sum(size for _, size in self.orphans)
        print("Total files in db: ", len(self.files_in_db))
        print("Total files in s3: ", len(self.files_in_s3))
        s3_size = sum(size for _, size in self.files_in_s3)
        s3_size = s3_size / (1024 * 1024)
        s3_size = round(s3_size, 2)
        print("Total size of files in s3: ", s3_size, "MB")
        print(f"Total orphans: {len(self.orphans)}")
        print(f"Total size of orphans: {total_size} bytes")
        print(f"Total size of orphans: {total_size/(1024*1024)} MB")

    def clean_orphans(self, delete_lote=1000):
        self.responses = delete_files(
            self.orphans, self.my_bucket, delete_lote)

    def copy_new_file(self, file_obj, new_file_path, is_clone=False):
        full_name = file_obj.file.name
        if len(new_file_path) > 254:
            print("Name too long:", new_file_path, "|", file_obj.id)
            return None
        if full_name == new_file_path:
            return None
        if self.s3_utils.check_exist(new_file_path):
            print("already exist:", new_file_path, "|", file_obj.id)
            return None

        # print(" new_file", new_file_path)
        # print("-" * 10)
        # continue
        try:
            self.s3_utils.change_storage_class(
                full_name, self.storage_name, path_destiny=new_file_path)
            count = self.dict_files_in_db.get(full_name, 0)
            if count == 1:
                self.s3_utils.delete_file(full_name)
            elif is_clone and count == 2:
                self.s3_utils.delete_file(full_name)
            else:
                print("El archivo no se borro:", full_name, "|", file_obj.id)

        except Exception as e:
            print("full_name", full_name, "|", file_obj.id)
            print(" new_file", new_file_path)
            print("error raro:\n", e)
            print("-" * 50)
        file_obj.file = new_file_path
        file_obj.save()
        return new_file_path

    def move_and_change_sheets(self, sheet_files, standard=False):
        self.storage_name = "STANDARD_IA" if standard else "GLACIER_IR"
        count = 0
        for sheet_file in sheet_files:
            count += 1
            if count % 59 == 0:
                print("count", count)
            elif not self.run:
                continue
            self.move_and_change_sheet(sheet_file)

    def move_and_change_sheet(self, sheet_file: SheetFile):
        from respond.models import set_upload_sheet_file_path
        from respond.data_file_mixins.base_transform import get_only_path_name

        if sheet_file.file_type == "clone":
            new_file_path = self.move_and_change_df(
                sheet_file.data_file, is_clone=True)
            if new_file_path and new_file_path != sheet_file.file:
                sheet_file.file = new_file_path
                sheet_file.save()
        # print("full_name", full_name, "|", sheet_file.id)
        else:
            petition = sheet_file.data_file.petition_file_control.petition
            file_name = get_only_path_name(sheet_file, petition)
            # print("file_name", file_name)
            new_file_path = set_upload_sheet_file_path(sheet_file, file_name)
            self.copy_new_file(sheet_file, new_file_path)
        # return new_file_path

    def move_and_change_df(self, data_file: DataFile, is_clone=False):
        from respond.models import set_upload_data_file_path
        from respond.data_file_mixins.base_transform import get_only_path_name
        import re

        petition = data_file.petition_file_control.petition
        file_name = get_only_path_name(data_file, petition)
        new_file_path = set_upload_data_file_path(data_file, file_name)
        if is_clone:
            # replace the start "data/" with "sheet/"
            sheet_path = re.sub(r"^data/", "sheet/", new_file_path)
            if self.s3_utils.check_exist(sheet_path):
                data_file.file = sheet_path
                data_file.save()
                return sheet_path
        return self.copy_new_file(data_file, new_file_path, is_clone)

    def change_sheet_files(self, provider_id):
        from respond.models import SheetFile
        base_files = SheetFile.objects.all()
        if provider_id:
            base_files = base_files.filter(data_file__provider_id=provider_id)
        transformed_files = base_files.filter(
            data_file__stage_id='transform', data_file__status_id='finished') \
            .distinct()
        print("transformed_files", transformed_files.count())
        pre_transformed_files = base_files.filter(
            data_file__stage_id='pre_transform', data_file__status_id='finished') \
            .distinct()
        print("pre_transformed_files", pre_transformed_files.count())
        discarded_files = base_files.filter(
            behavior__is_discarded=True).exclude(
            data_file__stage_id__in=['transform', 'pre_transform'],
            data_file__status_id='finished').distinct()
        print("discarded_files", discarded_files.count())
        other_files = base_files.exclude(
            data_file__stage_id__in=['transform', 'pre_transform'],
            data_file__status_id='finished') \
            .exclude(behavior__is_discarded=True).distinct()
        print("other_files", other_files.count())

        self.move_and_change_sheets(transformed_files, standard=False)
        self.move_and_change_sheets(pre_transformed_files, standard=False)
        self.move_and_change_sheets(discarded_files, standard=False)
        self.move_and_change_sheets(other_files, standard=True)


def delete_files(files, s3_bucket=None, delete_lote=1000):
    from django.conf import settings
    responses = []
    aws_location = getattr(settings, "AWS_LOCATION", "")
    can_delete_aws_storage_files = getattr(
        settings, "CAN_DELETE_AWS_STORAGE_FILES", False)
    if not can_delete_aws_storage_files:
        print("No se pueden borrar archivos en AWS")
        return []
    if not s3_bucket:
        import boto3
        bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
        aws_access_key_id = getattr(settings, "AWS_ACCESS_KEY_ID")
        aws_secret_access_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
        s3 = boto3.resource(
            's3', aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key)
        s3_bucket = s3.Bucket(bucket_name)

    for i in range(0, len(files), delete_lote):
        delete_objects = [
            {'Key': aws_location + key}
            for key, _ in files[i:i+delete_lote]
        ]
        response = s3_bucket.delete_objects(
            Delete={'Objects': delete_objects})
        responses.append(response)
    return responses
