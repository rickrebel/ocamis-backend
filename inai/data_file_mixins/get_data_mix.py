raws = {}


class ExtractorsMix:
    petition_file_control: None
    save_errors: classmethod
    final_path: str

    # def every_has_total_rows(self, task_params=None, **kwargs):
    #     data_file = self
    #     sample_data = data_file.sample_data
    #     need_recalculate = False
    #     if not sample_data:
    #         need_recalculate = True
    #     if not need_recalculate:
    #         for sheet_name, sheet_data in sample_data.items():
    #             if not sheet_data.get("total_rows"):
    #                 need_recalculate = True
    #                 break
    #     if need_recalculate:
    #         curr_kwargs = {
    #             "forced_save": True, "after_if_empty": "counting_from_aws"}
    #         all_tasks, all_errors, data_file = data_file.get_sample_data(
    #             task_params, **curr_kwargs)
    #         return all_tasks, all_errors, data_file
    #     return [], [], data_file

    # def counting_from_aws(self, task_params=None, **kwargs):
    #     from data_param.models import FileControl
    #     data_file, kwargs = self.corroborate_save_data(task_params, **kwargs)
    #     data_file, saved, errors = data_file.find_coincidences()
    #     if not saved and not errors:
    #         errors = ["No coincide con el formato del archivo (counting)"]
    #     if errors:
    #         data_file.save_errors(errors, "explore_fail")
    #     return [], errors, None

    def transform_file_in_data(
            self, type_explor, file_control=None, task_params=None):
        from category.models import FileFormat
        is_explore = bool(type_explor)
        data_file = self
        # is_auto = type_explor == 'auto_explore'
        status_error = 'explore|with_errors' if is_explore else 'extraction|with_errors'
        if not file_control:
            file_control = data_file.petition_file_control.file_control
        is_orphan = file_control.data_group.name == "orphan"
        new_task = None
        current_sheets = ["default"]
        same_suffix = True
        validated_data = {}
        if not is_orphan:
            if not file_control.file_format:
                errors = ["El grupo de control no tiene formato específico"]
                return None, errors, None
            same_suffix = data_file.suffix in file_control.file_format.suffixes
        if not same_suffix:
            # if type_explor == 'auto_explore':
            #     errors = ["No existe ningún grupo de control coincidente"]
            # else:
            #     errors = ["Formato especificado no coincide con el archivo"]
            return None, None, None
        elif data_file.suffix in FileFormat.objects.get(short_name='xls').suffixes:
            result, new_task = data_file.get_data_from_excel(
                type_explor, file_control=file_control, task_params=task_params)
            (validated_data, current_sheets, errors) = result
        elif data_file.suffix in ['.txt', '.csv']:
            validated_data, errors, new_task = data_file.get_data_from_file_simple(
                type_explor, file_control=file_control, task_params=task_params)
        else:
            errors = "No es un formato válido"
        if errors or new_task:
            if errors:
                data_file.save_errors(errors, status_error)
            return None, errors, new_task

        # if is_explore:
        #     data_file.sample_data = validated_data
        #     data_file.save()

        if type_explor == 'only_save' or type_explor == 'forced_save':
            return data_file, errors, new_task

        row_headers = file_control.row_headers or 0
        # for sheet_name, all_data in validated_data.items():
        new_validated_data = {}

        def calculate_aislated(headers):
            not_null_aislated = []
            some_null = False
            for header in headers[1:]:
                if not header:
                    some_null = True
                if some_null and header:
                    not_null_aislated.append(header)
            return not_null_aislated

        for sheet_name in validated_data.keys():
            try:
                curr_sheet = validated_data.get(sheet_name).copy()
            except Exception as e:
                raise e
            plus_rows = 0
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
                    # nulls = [header for header in headers[1:] if not header]
                    not_null_aislated = calculate_aislated(headers)
                    few_nulls = len(not_null_aislated) < 2
                    if not few_nulls and len(all_data) > row_headers:
                        plus_rows = 1
                        headers = all_data[row_headers]
                        not_null_aislated = calculate_aislated(headers)
                        # if nulls:
                        #    continue
                    few_nulls = len(not_null_aislated) < 2
                if (few_nulls and headers) or not row_headers:
                    # plus_cols = 0 if headers[0] else 1
                    # validated_data[sheet_name]["plus_columns"] = plus_cols
                    start_data = file_control.row_start_data - 1 + plus_rows
                    curr_sheet["plus_rows"] = plus_rows
                    data_rows = all_data[start_data:][:200]
                    curr_sheet["data_rows"] = data_rows
                    # curr_sheet["headers"] = headers[plus_cols:]
                    curr_sheet["headers"] = headers
                else:
                    print("No pasó las pruebas básicas -", sheet_name)
                    curr_sheet["headers"] = headers
                    curr_sheet["data_rows"] = all_data
                    # pendiente_hasta_aca = 0
            new_validated_data[sheet_name] = curr_sheet

        # if not is_explore:
        #     matched_rows = []
        #     for row in validated_rows:
        #         row = execute_matches(row, self)
        #         matched_rows.append(row)
        #     return matched_rows
        print("current_sheets", current_sheets)
        result = {
            "structured_data": new_validated_data,
            "current_sheets": current_sheets,
        }
        return result, [], None

    def get_data_from_excel(
            self, type_explor, file_control=None, task_params=None):
        from task.serverless import async_in_lambda
        from scripts.common import build_s3
        from scripts.common import explore_sheets
        is_explore = bool(type_explor)
        if is_explore:
            all_sheets = self.all_sample_data
        else:
            all_sheets = {}

        sheet_names = self.sheet_names_list
        
        if type_explor == 'only_save' or type_explor == 'forced_save':
            # has_sheet_names = bool(sheet_names)
            # if not has_sheet_names:
            params = {
                "final_path": self.final_path,
                "only_name": self.file.name,
                "s3": build_s3(),
            }
            task_params = task_params or {}
            new_task = async_in_lambda("xls_to_csv", params, task_params)
            return (all_sheets, [], []), new_task
            # else:
            #     return (all_sheets, sheet_names, []), None

        include_names, exclude_names, include_idx, exclude_idx = explore_sheets(
            file_control)
        print("include_names", include_names)
        print("exclude_names", exclude_names)
        print("include_idx", include_idx)
        print("exclude_idx", exclude_idx)

        filtered_sheets = []
        pending_sheets = []

        for position, sheet_name in enumerate(sheet_names, start=1):
            if include_names and sheet_name not in include_names:
                continue
            if exclude_names and sheet_name in exclude_names:
                continue
            if include_idx and position not in include_idx:
                continue
            if exclude_idx and position in exclude_idx:
                continue
            filtered_sheets.append(sheet_name)
            # xls.parse(sheet_name)
            if is_explore and sheet_name in all_sheets:
                if "all_data" in all_sheets[sheet_name]:
                    continue
            print("SE TUVO QUE LEER EL EXCEL DE NUEVO")
            pending_sheets.append(sheet_name)
            continue
        print("SÍ LLEGAMOS A VOLVER A CALCULAR LAS PESTAÑAS", filtered_sheets)
        return (all_sheets, filtered_sheets, []), None

    def explore_data_xls_after(self, parent_task=None, **kwargs):
        # params_after = {}
        # if parent_task:
        #     params_after = parent_task.params_after
        new_sheets = kwargs.get("new_sheets", {})
        all_sheet_names = kwargs.get("all_sheet_names", [])
        # delimiter = kwargs.get("delimiter")
        decode = kwargs.get("decode")
        if decode:
            file_control = self.petition_file_control.file_control
            if not file_control.decode and file_control.data_group.name != 'orphan':
                file_control.decode = decode
                file_control.save()
        self.sheet_names = all_sheet_names
        # current_sheets = params_after.get("current_sheets", [])
        # print(current_sheets)
        sample_data = self.sample_data or {}
        sample_data.update(new_sheets)
        self.sample_data = sample_data
        self.save()
        return [], [], self

    def build_sample_data_after(self, parent_task=None, **kwargs):
        from inai.models import SheetFile
        new_sheets = kwargs.get("new_sheets", {})
        sheet_count = len(new_sheets)
        for sheet_name, sheet_data in new_sheets.items():
            is_not_xls = sheet_count == 1 and sheet_name == "default"
            simple_path = self.file if is_not_xls else None
            file_type_id = "clone" if is_not_xls else "sheet"
            final_path = sheet_data.pop("final_path", simple_path)
            total_rows = sheet_data.pop("total_rows")
            SheetFile.objects.create(
                file=final_path,
                data_file=self,
                sheet_name=sheet_name,
                sample_data=sheet_data,
                file_type_id=file_type_id,
                total_rows=total_rows,
            )
        decode = kwargs.get("decode")
        if decode:
            file_control = self.petition_file_control.file_control
            if not file_control.decode and file_control.data_group.name != 'orphan':
                file_control.decode = decode
                file_control.save()
        if self.stage_id == "explore":
            self.status_id = "finished"
            self.save()
        return [], [], self

    def get_data_from_file_simple(
            self, type_explor, file_control=None, task_params=None):
        from task.serverless import async_in_lambda
        from scripts.common import build_s3
        from scripts.recipe_specials import special_issste

        errors = []
        is_explore = bool(type_explor)

        if type_explor == 'only_save' or type_explor == 'forced_save':
            params = {
                "file": self.file.name,
                "s3": build_s3(),
                "delimiter": file_control.delimiter,
            }
            task_params = task_params or {}
            # params_after = task_params.get("params_after", {})
            # params_after["next_"] = is_explore
            # task_params["params_after"] = params_after
            function_after = task_params.get(
                "function_after", "find_matches_in_file_controls")
            task_params["function_after"] = function_after
            errors = []
            async_task = async_in_lambda(
                "explore_data_simple", params, task_params)
            if not async_task:
                errors.append("No se pudo iniciar la tarea")
            return errors, [], async_task

        all_sheets = self.all_sample_data
        if is_explore and isinstance(all_sheets, dict):
            if "all_data" in all_sheets.get("default", {}):
                return all_sheets, errors, None

        print("ESTOY EN UN LUGAR QUE NO DEBERÍA DE ESTAR CSV")
        raise Exception("ESTOY EN UN LUGAR QUE NO DEBERÍA DE ESTAR CSV")
        # s3_client, dev_resource = start_session()
        # data = get_file(self, dev_resource)
        # if isinstance(data, dict):
        #     if data.get("errors", False):
        #         return False, data["errors"], None
        # data_rows = data.readlines()
        # total_rows = len(data_rows)
        # if is_explore:
        #     data_rows = data_rows[220]
        # validated_data_default = self.divide_rows(
        #     data_rows, file_control, is_explore=is_explore)
        # validated_data = {
        #     "default": {
        #         "all_data": validated_data_default[:200],
        #         "total_rows": total_rows,
        #     }
        # }
        #
        # is_issste = file_control.petition.agency.institution.code == 'ISSSTE'
        # if is_issste:
        #     new_tasks, errors, data = special_issste(data, file_control, is_issste)
        #
        # return validated_data, None, None

    # RICK 19: Esto debería eliminarse
    def divide_rows(self, data_rows, file_control, is_explore=False):
        global raws
        from data_param.models import NameColumn
        current_columns = NameColumn.objects.filter(
            file_control=file_control)
        columns_count = current_columns.filter(
            position_in_data__isnull=False).count()
        structured_data = []
        missing_data = []
        # print("delimiter", delimiter)
        # encoding = "utf-8"
        try:
            sample = data_rows[3]
        except Exception as e:
            sample = ""
        is_byte = isinstance(sample, bytes)
        is_latin = False
        delimiter = file_control.delimiter or "|"
        for row_seq, row in enumerate(data_rows, 1):
            # if row_seq < 5:
            #    print(row_seq, row)
            posible_latin = False
            if is_byte:
                if is_latin:
                    row = row.decode("latin-1")
                else:
                    try:
                        row = row.decode("utf-8")
                    except:
                        posible_latin = True
                    if posible_latin:
                        try:
                            row = row.decode("latin-1")
                            is_latin = True
                        except Exception as e:
                            print(e)
                            row = str(row)
            else:
                row = str(row)
            row_data = row.split(delimiter)
            if is_explore or len(row_data) == columns_count:
                # row_data.insert(0, row_seq)
                structured_data.append(row_data)
            else:
                errors = ["Conteo distinto de Columnas: %s de %s" % (
                    len(row_data), columns_count)]
                missing_data.append([self.id, row_data, row_seq, errors])
            # if row_seq < 5:
            #    print(row_data)

        raws["missing_r"] = missing_data

        return structured_data
