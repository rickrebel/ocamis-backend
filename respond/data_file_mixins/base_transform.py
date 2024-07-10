from respond.models import DataFile, LapSheet


def sheet_name_to_file_name(sheet_name):
    import re
    valid_characters = re.sub(r'[\\/:*?"<>|]', '_', sheet_name)
    valid_characters = valid_characters.strip()
    valid_characters = re.sub(r'\s+', ' ', valid_characters)
    valid_characters = valid_characters.replace(' ', '_')

    return valid_characters


class BaseDataFile:

    def __init__(self, data_file: DataFile, task_params=None):
        self.data_file = data_file
        self.task_params = task_params


class BaseTransform(BaseDataFile):

    def __init__(self, data_file: DataFile, task_params=None):
        super().__init__(data_file, task_params)
        self.is_prepare = False
        self.init_data = {}
        self.all_tasks = []
        self.file_control = data_file.petition_file_control.file_control
        full_name = data_file.file.name
        if "/reply_file_" in full_name:
            file_name = full_name.rsplit('/reply_file_', 1)[-1]
        else:
            file_name = full_name.rsplit('/', 1)[-1]
        self.file_name = file_name.replace(".", "_")

    def calculate_sheets(self):
        from classify_task.models import Stage, StatusTask
        filter_sheets = self.data_file.filtered_sheets
        procesable_sheets = self.data_file.sheet_files.filter(
            matched=True, sheet_name__in=filter_sheets)
        transform_stage = Stage.objects.get(name="transform")
        finish_status = StatusTask.objects.get(name="finished")
        remaining_prev_stage = procesable_sheets.filter(
            stage__order__lt=transform_stage.order)
        remaining_same_stage = procesable_sheets.filter(
            stage=transform_stage, status__order__lt=finish_status.order)
        remaining_sheets = remaining_prev_stage | remaining_same_stage
        if remaining_sheets.exists():
            final_sheets = remaining_sheets
        else:
            final_sheets = procesable_sheets
        first_sheet = final_sheets.first()
        is_split = False
        if first_sheet:
            file_type = first_sheet.file_type_id
            is_split = file_type == 'split'
        files_to_process = []
        for idx, sheet_file in enumerate(final_sheets):
            init_data = self.init_data.copy()
            if idx and is_split and not self.is_prepare:
                init_data["row_start_data"] = 1
            init_data["sheet_name"] = sheet_file.sheet_name
            init_data["sheet_file_id"] = sheet_file.id
            sheet_name2 = sheet_name_to_file_name(sheet_file.sheet_name)
            init_data["final_path"] = self.final_path.replace(
                "SHEET_NAME", sheet_name2)
            sheet = {
                "params": {
                    "init_data": init_data,
                    "file": sheet_file.file.name,
                },
                "sheet_file": sheet_file,
            }
            files_to_process.append(sheet)

        return files_to_process

    def send_lambda(self, function_name, params):
        from task.serverless import async_in_lambda
        async_task = async_in_lambda(function_name, params, self.task_params)
        if async_task:
            self.all_tasks.append(async_task)
