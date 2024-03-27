from scripts.common import text_normalizer


class BuildComplexHeaders:
    from respond.models import DataFile

    def __init__(self, data_file: DataFile):
        self.data_file = data_file
        self.complex_headers = []
        self.provider_uniques = {}
        self.unique_std_names = {}

    def __call__(self, *args, **kwargs):
        from data_param.models import NameColumn

        data, errors, new_task = self.data_file\
            .transform_file_in_data('auto_explore')
        if errors:
            return self.send_errors(errors, "explore|with_errors")

        # valid_fields = [
        #     "name_in_data", "column_type", "final_field",
        #     "final_field__parameter_group", "data_type"]
        validated_data = data["structured_data"]
        current_sheets = data["current_sheets"]
        first_valid_sheet = None
        for sheet_name in current_sheets:
            sheet_data = validated_data[sheet_name]
            # if getattr(sheet_data, "headers"):
            if "headers" in sheet_data and sheet_data["headers"]:
                first_valid_sheet = sheet_data
                break
        if not first_valid_sheet:
            first_valid_sheet = validated_data[current_sheets[0]]
            if not first_valid_sheet:
                return self.send_errors(
                    ["WARNING: No se encontró algo que coincidiera"])
            else:
                return self.build_first_headers(first_valid_sheet)
        try:
            df_headers = first_valid_sheet["headers"]
            file_control = self.data_file.petition_file_control.file_control
            data_groups = [file_control.data_group.name, 'catalogs']
            # print(data_groups)
            std_names_headers = [
                text_normalizer(head, True) for head in df_headers]
            worked_name_columns = NameColumn.objects.filter(
                final_field__isnull=False,
                name_in_data__isnull=False,
                std_name_in_data__in=std_names_headers,
                final_field__parameter_group__data_group__name__in=data_groups
            ).prefetch_related(
                'final_field__parameter_group', 'column_transformations',
                'file_control__agency')
            provider_id = file_control.agency.provider_id
            self.build_unique_dicts(worked_name_columns, provider_id)
            self.find_header_values(df_headers)
            return self.send_results(first_valid_sheet)

        except Exception as e:
            return self.send_errors([str(e)])

    def send_results(self, valid_sheet):
        valid_sheet["complex_headers"] = self.complex_headers
        return None, None, valid_sheet

    def build_first_headers(self, first_valid_sheet):
        real_headers = first_valid_sheet["all_data"][0]
        self.complex_headers = [
            {"position_in_data": posit}
            for posit, head in enumerate(real_headers, start=1)]
        return self.send_results(first_valid_sheet)

    def build_unique_dicts(self, worked_name_columns, provider_id):
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

    def find_header_values(self, df_headers):
        for (position, header) in enumerate(df_headers, start=1):
            std_header = text_normalizer(header, True)
            found_match = self.find_match(std_header)
            base_dict = {
                "position_in_data": position, "name_in_data": header}
            base_dict.update(found_match)
            self.complex_headers.append(base_dict)

    def find_match(self, std_header):
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
                        first_match = [
                            val for val in vals_matched if val[0] == mode_key]
                        return first_match[0][1]
        return {}

    def send_errors(self, errors, error_text: str = None) -> tuple:
        print("ERRORS", errors)
        if error_text:
            self.data_file.save_errors(errors, error_text)
        return None, errors, None
