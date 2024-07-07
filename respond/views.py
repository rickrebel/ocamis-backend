from scripts.common import start_session, create_file
from scripts.common import build_s3
from task.aws.common import BotoUtils


class SampleFile:
    def __init__(self, data_file, sample_data):
        s3 = build_s3()
        self.s3_utils = BotoUtils(s3)

    def get_sample_file(self, sheet_file):
        # self.s3_utils.get_json_file(sheet_file.sample_file)
        self.s3_utils.get_csv_lines(sheet_file)

    def create_sample_file(self, sheet_file):
        import json

        dump_sample = json.dumps(sheet_file.sample_data)
        final_path = f"catalogs/{sheet_file.data_file.provider.acronym}" \
                     f"/sample_file_{sheet_file.id}.json"
        self.s3_utils.save_file_in_aws(
            dump_sample, final_path, "text/json")
