
from datetime import datetime
from typing import Any, Dict, List

from django.conf import settings


class CleanBucket:
    my_bucket: Any
    files_models_in_db: Dict[str, List] = {}
    aws_location: str = "data_files/"
    files_in_s3: List = []
    files_in_db: List = []
    orphans: List = []
    responses: List = []

    def __init__(self, aws_location="", limit=10000):
        import boto3
        from django.conf import settings
        bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
        aws_access_key_id = getattr(settings, "AWS_ACCESS_KEY_ID")
        aws_secret_access_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
        s3 = boto3.resource(
            's3', aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key)
        self.my_bucket = s3.Bucket(bucket_name)
        if "data_file" in aws_location:
            self.aws_location = aws_location
        # self.aws_location = aws_location or self.aws_location
        self.excluded_dirs = [
            "admin/", "aws_errors/", "cat_images/", "ckeditor/", "experiment/",
            "logos/", "mat_views/", "profile_images/", "rest_framework/"]

    def __call__(self):
        self.get_files_in_db()
        self.get_files_in_s3()
        self.find_orphans()
        print("Orphans found: ", datetime.now().strftime("%H:%M:%S"))
        self.report_orphans()

    def get_files_in_db(self):
        print("Getting files in db: ", datetime.now().strftime("%H:%M:%S"))
        from respond.models import TableFile
        from respond.models import SheetFile
        from respond.models import DataFile
        from respond.models import ReplyFile
        model_files = [TableFile, SheetFile, DataFile, ReplyFile]
        for model in model_files:
            self.get_files_in_model(model)
        self.files_in_db = list(set(self.files_in_db))

    def get_files_in_model(self, model):
        model_file_query = model.objects.filter(file__isnull=False)
        model_count = model_file_query.count()
        for i in range(0, model_count, 1000):
            self.files_in_db.extend(
                model_file_query.values_list('file', flat=True)[i:i+1000])

    def get_files_in_s3(self):
        print("Getting files in s3: ", datetime.now().strftime("%H:%M:%S"))
        all_bucket_files = self.my_bucket.objects.filter(
            Prefix=self.aws_location)
        for bucket_obj in all_bucket_files:
            bucket_obj_key = bucket_obj.key.replace(self.aws_location, '')
            if any(
                bucket_obj_key.startswith(excluded_dir)
                for excluded_dir in self.excluded_dirs
            ):
                continue
            self.files_in_s3.append((bucket_obj_key, bucket_obj.size))

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
        self.responses = []
        can_delete_aws_storage_files = getattr(
            settings, "CAN_DELETE_AWS_STORAGE_FILES", False)
        if not can_delete_aws_storage_files:
            print("No se pueden borrar archivos en AWS")
            return

        for i in range(0, len(self.orphans), delete_lote):
            delete_objects = [
                {'Key': self.aws_location + key}
                for key in self.orphans[i:i+delete_lote]
            ]
            response = self.my_bucket.delete_objects(
                Delete={'Objects': delete_objects})
            self.responses.append(response)
