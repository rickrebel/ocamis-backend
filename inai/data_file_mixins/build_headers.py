class BuildComplexHeaders:
    from inai.models import DataFile

    def __init__(self, data_file: DataFile):
        self.data_file = data_file

    def __call__(self, *args, **kwargs):
        from statistics import mode
        from data_param.models import NameColumn
        from scripts.common import text_normalizer
        from data_param.api.serializers import NameColumnHeadersSerializer

        all_errors = []
        data, errors, new_task = self.data_file\
            .transform_file_in_data('auto_explore')
        if errors:
            all_errors.extend(errors)
            self.data_file.save_errors(all_errors, "explore|with_errors")
            return None, errors, None

        # valid_fields = [
        #     "name_in_data", "column_type", "final_field",
        #     "final_field__parameter_group", "data_type"]
        validated_data = data["structured_data"]
        current_sheets = data["current_sheets"]
        first_valid_sheet = None
        for sheet_name in current_sheets:
            sheet_data = validated_data[sheet_name]
            if "headers" in sheet_data and sheet_data["headers"]:
                first_valid_sheet = sheet_data
                break
        if not first_valid_sheet:
            first_valid_sheet = validated_data[current_sheets[0]]
            if not first_valid_sheet:
                errors = ["WARNING: No se encontró algo que coincidiera"]
                return None, errors, None
            else:
                prov_headers = first_valid_sheet["all_data"][0]
                first_valid_sheet["complex_headers"] = [
                    {"position_in_data": posit}
                    for posit, head in enumerate(prov_headers, start=1)]
                return None, None, first_valid_sheet
        try:
            headers = first_valid_sheet["headers"]
            complex_headers = []
            file_control = self.data_file.petition_file_control.file_control
            data_groups = [file_control.data_group.name, 'catalogs']
            # print(data_groups)
            std_names_headers = [text_normalizer(head, True) for head in headers]
            worked_name_columns = NameColumn.objects.filter(
                final_field__isnull=False,
                name_in_data__isnull=False,
                std_name_in_data__in=std_names_headers,
                final_field__parameter_group__data_group__name__in=data_groups
            ).prefetch_related(
                'final_field__parameter_group', 'column_transformations',
                'file_control__agency')
            # ).values(*valid_fields)
            all_name_columns = NameColumnHeadersSerializer(
                worked_name_columns, many=True).data
            entity_id = file_control.agency.entity_id
            # unique_std_names = {std_name: {"uniques":[]}
            #                     for std_name in std_names_headers}
            unique_std_names = {}
            entity_uniques = {}
            for name_col in all_name_columns:
                std_name = name_col["std_name_in_data"]
                unique_name = (
                    f'{std_name}-{name_col["final_field"]}-'
                    f'{name_col["parameter_group"]}')
                # base_new = {"data": name_col, "uniques": []}
                if not unique_std_names.get(std_name):
                    unique_std_names[std_name] = []
                unique_std_names[std_name].append((unique_name, name_col))
                # unique_std_names[std_name_in_data][unique_name] = name_col
                if name_col["entity"] == entity_id:
                    if not entity_uniques.get(std_name):
                        entity_uniques[std_name] = []
                    entity_uniques[std_name].append((unique_name, name_col))

            for (position, header) in enumerate(headers, start=1):
                std_header = text_normalizer(header, True)
                base_dict = {
                    "position_in_data": position, "name_in_data": header}

                def build_dict(vals: list):
                    count_vals = len(vals)
                    if count_vals == 1:
                        return vals[0][1]
                    else:
                        keys = [val[0] for val in vals]
                        mode_key = mode(keys)
                        proportion = keys.count(mode_key) / count_vals
                        if proportion >= 0.5:
                            first_match = [
                                val for val in vals if val[0] == mode_key]
                            return first_match[0][1]

                found_values = None
                if vals_matched := entity_uniques.get(std_header, False):
                    found_values = build_dict(vals_matched)
                if not found_values:
                    if vals_matched2 := unique_std_names.get(std_header, False):
                        found_values = build_dict(vals_matched2)
                if found_values:
                    base_dict.update(found_values)
                complex_headers.append(base_dict)

            first_valid_sheet["complex_headers"] = complex_headers
        except Exception as e:
            print("HUBO UN ERRORZASO")
            print(e)
        # print(data["structured_data"][:6])
        return None, None, first_valid_sheet
