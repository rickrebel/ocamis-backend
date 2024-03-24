from respond.models import DataFile, LapSheet
from inai.data_file_mixins.base_transform import BaseTransform


class Intermediary(BaseTransform):

    def __init__(self, data_file: DataFile, task_params=None):
        super().__init__(data_file, task_params)
        from inai.models import set_upload_path
        only_name = f"{self.file_name}_SHEET_NAME_intermediary"
        self.final_path = set_upload_path(self.data_file, only_name)
        self.task_params["function_after"] = "save_new_split_files"

    def split_columns(self):
        from data_param.models import NameColumn
        destinations = NameColumn.objects \
            .filter(file_control=self.file_control) \
            .values_list("destination", flat=True)
        self.init_data["destinations"] = list(destinations)
        sheets_to_process = self.calculate_sheets()
        for sf in sheets_to_process:
            print("sf['params']", sf["params"])
            self.send_lambda("split_horizontal", sf["params"])
        return self.all_tasks, [], self.data_file
