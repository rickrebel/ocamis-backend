from scripts.common import build_s3
from task.aws.common import BotoUtils
from respond.models import SheetFile, DataFile


class SampleFile:

    def __init__(self):
        s3 = build_s3()
        self.s3_utils = BotoUtils(s3)
        self.sample_data = None
        self.file_obj = None
        self.final_path = None

    def get_json_content(self, file_path):
        # import json
        if file_path:
            self.final_path = file_path
        if not self.final_path:
            raise ValueError("No file path provided")
        # json_lines = self.s3_utils.get_csv_lines(self.final_path)
        # return json.loads(json_lines.read())
        json_lines = self.s3_utils.get_json_file(self.final_path)
        return json_lines

    def get_sample(self, file_obj) -> dict:
        if file_obj.sample_file:
            return self.get_json_content(file_obj.sample_file.name)
        elif file_obj.sample_data:
            sample_data = file_obj.sample_data.copy()
            return sample_data
        else:
            return {}

    def get_file_path(self, file_obj):
        if file_obj.sample_file:
            self.final_path = file_obj.sample_file.name
        else:
            self.create_file(file_obj)
        return self.final_path

    def build_path_name(self, file_obj=None, cat_name=None):
        if file_obj:
            self.file_obj = file_obj
        if not self.file_obj and not file_obj:
            raise ValueError("No file object provided")
        is_data_file = isinstance(self.file_obj, DataFile)
        is_sheet_file = isinstance(self.file_obj, SheetFile)
        if is_data_file:
            provider = self.file_obj.provider
        elif is_sheet_file:
            provider = self.file_obj.data_file.provider
        else:
            raise ValueError("Invalid file object")
        if not cat_name:
            cat_name = "sheet_samples" if is_data_file else "data_samples"
        self.final_path = f"{cat_name}/{provider.acronym}" \
                          f"/sample_file_{self.file_obj.id}.json"
        return self.final_path

    def create_file(self, file_obj=None, cat_name=None, sample_data=None):
        import json
        if file_obj:
            self.file_obj = file_obj
        if not self.file_obj and not file_obj:
            raise ValueError("No file object provided")
        if sample_data:
            self.sample_data = sample_data

        if not self.sample_data:
            self.sample_data = self.file_obj.sample_data
        if not self.sample_data:
            raise ValueError("No sample data provided")
        dump_sample = json.dumps(self.sample_data)
        self.build_path_name(cat_name=cat_name)
        self.s3_utils.save_json_file(dump_sample, self.final_path)
        return self.final_path

    def save_sample(self, file_obj, sample_data):
        self.file_obj = file_obj
        self.sample_data = sample_data

        file_obj.sample_data = self.sample_data
        self.create_file()
        file_obj.sample_file = self.final_path
        file_obj.save()

    # def get_many_samples(self, sheet_files: QuerySet[SheetFile]) -> dict:
    def get_sheet_samples(self, data_file: DataFile) -> dict:
        sheets_data = {}
        for sheet_file in data_file.sheet_files.all():
            sample = self.get_sample(sheet_file)
            sample.update({"file_type": sheet_file.file_type})
            sheets_data[sheet_file.sheet_name] = sample
        return sheets_data
