from django.conf import settings
from respond.models import DataFile, LapSheet
from task.base_views import TaskBuilder


def build_copy_sql_aws(table_file, model_in_db, columns_join):
    bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
    aws_location = getattr(settings, "AWS_LOCATION")
    region_name = getattr(settings, "AWS_S3_REGION_NAME")
    access_key = getattr(settings, "AWS_ACCESS_KEY_ID")
    secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
    path = table_file.file.name
    # encoding = "LATIN1" if self.file_control.decode == "latin-1" else "UTF8"
    encoding = "UTF8"
    return f"""
        SELECT aws_s3.table_import_from_s3(
            '{model_in_db}',
            '{columns_join}',
            '(format csv, header true, delimiter "|", encoding "{encoding}")',
            '{bucket_name}',
            '{aws_location}/{path}',
            '{region_name}',
            '{access_key}',
            '{secret_key}'
        )
    """


class Insert:

    def __init__(self, data_file: DataFile, task_params=None):
        from .matches_mix import get_models_of_app, field_of_models
        self.task_params = task_params
        self.data_file = data_file
        self.file_control = data_file.petition_file_control.file_control
        self.agency = self.file_control.agency
        self.editable_models = get_models_of_app("med_cat")
        self.editable_models += get_models_of_app("formula")
        self.model_fields = {model["name"]: field_of_models(model)
                             for model in self.editable_models}

    def build_copy_sql_local(self, table_file, model_in_db, columns_join):
        # from scripts.common import get_file, start_session
        # s3_client, dev_resource = start_session()
        # data = get_file(self, dev_resource).read()
        path = table_file.file.url
        # artificial_path = 'C:\\Users\\Ricardo\\Downloads\\diagnosis_3772_default_lap0.csv'
        artificial_path = 'diagnosis_3772_default_lap0.csv'
        # "COPY temp_doctors (hash_id, full_name, medical_speciality, institution_id) FROM
        # '/path/to/input_doctors.csv' WITH (FORMAT CSV, HEADER)
        encoding = "LATIN1" if self.file_control.decode == "latin-1" else "UTF8"
        return f"""
            COPY {model_in_db} ({columns_join})
            FROM '{artificial_path}'
            WITH (FORMAT CSV, HEADER, ENCODING {encoding})
        """
