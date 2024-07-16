from scripts.common import text_normalizer
from task.base_views import TaskBuilder
from respond.models import DataFile
from task.helpers import HttpResponseError
from respond.data_file_mixins.explore_mix_real import ExploreRealMix


class BuildComplexHeaders(ExploreRealMix):

    def __init__(self, data_file: DataFile, base_task: TaskBuilder = None):
        # self.data_file = data_file
        # self.base_task = base_task
        super().__init__(data_file, base_task=base_task, want_response=True)
        self.complex_headers = []
        self.provider_uniques = {}
        self.unique_std_names = {}

    def __call__(self, *args, **kwargs):
        from data_param.models import NameColumn

        # De acá obtendremos self.file_control
        full_sheet_data, filtered_sheets = self.get_data_from_file()
        # try:
        #     full_sheet_data, filtered_sheets = self.get_data_from_file()
        # except HttpResponseError as e:
        #     if e.errors:
        #         self.data_file.save_errors(e.errors, "explore|with_errors")
        #     return self.base_task.add_errors_and_raise(e.errors)

        first_valid_sheet = None
        for sheet_name in filtered_sheets:
            sheet_data = full_sheet_data[sheet_name]
            # if getattr(sheet_data, "headers"):
            if "headers" in sheet_data and sheet_data["headers"]:
                first_valid_sheet = sheet_data
                break
        if not first_valid_sheet:
            first_valid_sheet = full_sheet_data[filtered_sheets[0]]
            if not first_valid_sheet:
                error = "WARNING: No se encontró algo que coincidiera"
                self.base_task.add_errors_and_raise([error])
            else:
                return self._build_first_headers(first_valid_sheet)
        try:
            df_headers = first_valid_sheet["headers"]
            data_groups = [self.file_control.data_group_id, 'catalogs']
            # print(data_groups)
            std_names_headers = [
                text_normalizer(head, True) for head in df_headers]
            worked_name_columns = NameColumn.objects.filter(
                final_field__isnull=False,
                name_in_data__isnull=False,
                std_name_in_data__in=std_names_headers,
                final_field__parameter_group__data_group_id__in=data_groups
            ).prefetch_related(
                'final_field__parameter_group', 'column_transformations',
                'file_control__agency')
            provider_id = self.file_control.agency.provider_id
            self._build_unique_dicts(worked_name_columns, provider_id)
            self._find_header_values(df_headers)
            return self._send_results(first_valid_sheet)

        except Exception as e:
            error = f"ERROR: No se pudo construir los headers: {str(e)}"
            self.base_task.add_errors_and_raise([error])

    def _send_results(self, valid_sheet):
        valid_sheet["complex_headers"] = self.complex_headers
        return valid_sheet

    def _build_first_headers(self, first_valid_sheet):
        real_headers = first_valid_sheet["all_data"][0]
        self.complex_headers = [
            {"position_in_data": posit}
            for posit, head in enumerate(real_headers, start=1)]
        return self._send_results(first_valid_sheet)

    def _build_unique_dicts(self, worked_name_columns, provider_id):
        from data_param.api.serializers import NameColumnHeadersSerializer
        saved_name_columns = NameColumnHeadersSerializer(
            worked_name_columns, many=True).data

        for name_col in saved_name_columns:
            std_name = name_col["std_name_in_data"]
            unique_name = ((
                f'{std_name}-{name_col["final_field"]}-'
                f'{name_col["parameter_group"]}'), name_col)
            self.unique_std_names.setdefault(std_name, [])
            self.unique_std_names[std_name].append(unique_name)
            if name_col["provider"] == provider_id:
                self.provider_uniques.setdefault(std_name, [])
                self.provider_uniques[std_name].append(unique_name)

    def _find_header_values(self, df_headers):
        for (position, header) in enumerate(df_headers, start=1):
            std_header = text_normalizer(header, True)
            found_match = self._find_match(std_header)
            base_dict = {"position_in_data": position, "name_in_data": header}
            base_dict.update(found_match)
            self.complex_headers.append(base_dict)

    def _find_match(self, std_header):
        from statistics import mode
        dicts = [self.provider_uniques, self.unique_std_names]
        for uniques_dict in dicts:
            if vals_matched := uniques_dict.get(std_header, False):
                count_vals = len(vals_matched)
                if count_vals == 1:
                    return vals_matched[0][1]
                else:
                    keys = [val[0] for val in vals_matched]
                    mode_key = mode(keys)
                    proportion = keys.count(mode_key) / count_vals
                    if proportion >= 0.5:
                        first_match = [val for val in vals_matched
                                       if val[0] == mode_key]
                        return first_match[0][1]
        return {}
