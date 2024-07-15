from respond.models import DataFile
from task.base_views import TaskBuilder
from category.models import FileFormat
from respond.views import SampleFile
from data_param.models import FileControl
from typing import Any, Optional
raws = {}


class ExtractorRealMix:

    xls_suffixes = FileFormat.objects.get(short_name="xls").suffixes

    def __init__(self, data_file: DataFile, task_params=None,
                 base_task: TaskBuilder = None, want_response=True):
        self.data_file = data_file
        self.task_params = task_params
        self.base_task = base_task
        self.file_control: Optional[FileControl] = None
        self.want_response = want_response

    def _set_file_control(self, file_control):
        if file_control:
            if isinstance(file_control, int):
                self.file_control = FileControl.objects.get(id=file_control)
            elif isinstance(file_control, FileControl):
                self.file_control = file_control
            else:
                raise ValueError(
                    "file_control debe ser un entero o un objeto FileControl")
        elif not self.file_control:
            self.file_control = self.data_file.petition_file_control.file_control

    def _get_type_format(self):
        is_orphan = self.file_control.data_group_id == "orphan"

        error = None
        if not is_orphan:
            file_format = self.file_control.file_format
            if not file_format:
                error = "El grupo de control no tiene formato específico"
            if self.data_file.suffix not in file_format.suffixes:
                error = "Formato especificado no coincide con el archivo"
        if error:
            pass
        elif self.data_file.suffix in self.xls_suffixes:
            return 'excel'
        elif self.data_file.suffix in ['.txt', '.csv']:
            return 'simple'
        else:
            error = "No es un formato válido"
        if self.want_response:
            self.data_file.save_errors([error], 'explore|with_errors')
            self.base_task.add_errors_and_raise([error])
        return None

    # antes convert_file_in_data
    def build_data_from_file(self, file_control_id: int = None, task_kwargs=None):

        self._set_file_control(file_control_id)
        type_format = self._get_type_format()
        function_name, params = self._assemble_params(type_format)
        if not task_kwargs:
            task_kwargs = {}
        function_after = task_kwargs.get(
            "function_after", "find_matches_between_controls")
        params_after = task_kwargs.get("params_after", {})
        convert_task = TaskBuilder(
            function_name=function_name, parent_class=self.base_task,
            function_after=function_after, params_after=params_after,
            models=[self.data_file], params=params)
        convert_task.async_in_lambda()

    def _assemble_params(self, type_format: str) -> tuple[str, dict]:
        if type_format == 'excel':
            function_name = "xls_to_csv"
            params = {
                "final_path": self.data_file.final_path,
                "only_name": self.data_file.file.name,
            }
        else:  # elif type_format == 'simple':
            function_name = "explore_data_simple"
            decode = self.file_control.decode
            sample_file = SampleFile()
            params = {
                "file": self.data_file.file.name,
                "delimiter": self.file_control.delimiter,
                "sample_path": sample_file.build_path_name(self.data_file)
            }
        return function_name, params

    def get_data_from_file(self, file_control=None):

        self._set_file_control(file_control)
        type_format = self._get_type_format()
        sample_file = SampleFile()
        sheets_data = sample_file.get_sheet_samples(self.data_file)
        if type_format == 'excel':
            filtered_sheets = self._get_data_excel()
        elif type_format == 'simple':
            filtered_sheets = self._get_data_simple(sheets_data)
        else:
            return None
        row_headers = self.file_control.row_headers or 0
        # for sheet_name, all_data in validated_data.items():
        new_validated_data = {}

        def calculate_isolated(current_headers):
            not_null_alone = []
            some_null = False
            for header in current_headers[1:]:
                if not header:
                    some_null = True
                if some_null and header:
                    not_null_alone.append(header)
            return not_null_alone

        for sheet_name in validated_data.keys():
            try:
                curr_sheet = validated_data.get(sheet_name).copy()
            except Exception as e:
                raise e
            try:
                all_data = curr_sheet.get("all_data")
            except Exception as e:
                print("------ERROR EN OBTENER ALL_DATA-------")
                print(sheet_name, e)
                raise e
            if "headers" not in curr_sheet:
                few_nulls = False
                headers = []
                if row_headers and len(all_data) > row_headers - 1:
                    headers = all_data[row_headers - 1]
                    not_null_isolated = calculate_isolated(headers)
                    few_nulls = len(not_null_isolated) < 4
                if (few_nulls and headers) or not row_headers:
                    start_data = self.file_control.row_start_data - 1
                    data_rows = all_data[start_data:][:200]
                    curr_sheet["data_rows"] = data_rows
                    curr_sheet["headers"] = headers
                else:
                    print("No pasó las pruebas básicas -", sheet_name)
                    curr_sheet["headers"] = headers
                    curr_sheet["data_rows"] = all_data
            new_validated_data[sheet_name] = curr_sheet

        print("filtered_sheets", filtered_sheets)
        return {
            "structured_data": new_validated_data,
            "current_sheets": filtered_sheets,
        }

    def _get_data_excel(self) -> list:
        sheet_names = self.data_file.sheet_names_list

        incl_names, excl_names, incl_idx, excl_idx = self._explore_sheets()

        filtered_sheets = []
        for position, sheet_name in enumerate(sheet_names, start=1):
            if incl_names and sheet_name not in incl_names:
                continue
            if excl_names and sheet_name in excl_names:
                continue
            if incl_idx and position not in incl_idx:
                continue
            if excl_idx and position in excl_idx:
                continue
            filtered_sheets.append(sheet_name)
        return filtered_sheets

    def _explore_sheets(self) -> tuple:
        from data_param.models import Transformation
        file_transformations = Transformation.objects.filter(
            file_control=self.file_control,
            clean_function__name__icontains="_tabs_").prefetch_related(
            "clean_function")
        include_names = exclude_names = include_idx = exclude_idx = None

        for transform in file_transformations:
            current_values = transform.addl_params["value"].split(",")
            func_name = transform.clean_function.name
            all_names = [name.upper().strip() for name in current_values]
            if func_name == 'include_tabs_by_name':
                include_names = all_names
            elif func_name == 'exclude_tabs_by_name':
                exclude_names = all_names
            elif func_name == 'include_tabs_by_index':
                include_idx = [int(val.strip()) for val in current_values]
            elif func_name == 'exclude_tabs_by_index':
                exclude_idx = [int(val.strip()) for val in current_values]

        return include_names, exclude_names, include_idx, exclude_idx

    def _get_data_simple(self, sheets_data: dict) -> list:

        if isinstance(sheets_data, dict):
            if "all_data" in sheets_data.get("default", {}):
                return ['default']

            all_keys = list(sheets_data.keys())
            first_sheet_name = next(iter(all_keys), None)
            if "all_data" in sheets_data.get(first_sheet_name, {}):
                return all_keys
