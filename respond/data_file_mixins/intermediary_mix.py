from respond.models import DataFile, set_upload_data_file_path
from respond.data_file_mixins.base_transform import (
    BaseTransform, get_only_path_name)
from task.builder import TaskBuilder


class Intermediary(BaseTransform):

    def __init__(self, data_file: DataFile, base_task: TaskBuilder = None):
        super().__init__(data_file, base_task=base_task)
        file_name = get_only_path_name(self.data_file)
        self.file_name = file_name.replace(".", "_")
        only_name = (f"{self.file_name}_df_{self.data_file.id}"
                     f"_SHEET_NAME_intermediary")
        self.final_path = set_upload_data_file_path(self.data_file, only_name)

    def split_columns(self):
        from data_param.models import NameColumn
        destinations = NameColumn.objects \
            .filter(file_control=self.file_control) \
            .values_list("destination", flat=True)
        self.init_data["destinations"] = list(destinations)
        sheets_to_process = self.calculate_sheets()
        for sf in sheets_to_process:
            params = sf.get("params", {})
            sf_task = TaskBuilder(
                "split_horizontal", function_after="save_new_split_files",
                models=[sf], parent_task=self.base_task.main_task,
                params=params)
            sf_task.async_in_lambda()
