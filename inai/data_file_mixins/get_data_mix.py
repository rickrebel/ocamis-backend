raws = {}


class ExtractorsMix:
    petition_file_control: None
    final_path: str

    def transform_file_in_data(
            self, type_explor, file_control=None, task_params=None):
        print("transform_file_in_data", type_explor)
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
             result = data_file.get_data_from_file_simple(
                type_explor, file_control=file_control, task_params=task_params)
             validated_data, current_sheets, errors, new_task = result
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
            not_null_allone = []
            some_null = False
            for header in headers[1:]:
                if not header:
                    some_null = True
                if some_null and header:
                    not_null_allone.append(header)
            return not_null_allone

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
                    not_null_aislated = calculate_aislated(headers)
                    few_nulls = len(not_null_aislated) < 4
                if (few_nulls and headers) or not row_headers:
                    start_data = file_control.row_start_data - 1 + plus_rows
                    curr_sheet["plus_rows"] = plus_rows
                    data_rows = all_data[start_data:][:200]
                    curr_sheet["data_rows"] = data_rows
                    curr_sheet["headers"] = headers
                else:
                    print("No pasó las pruebas básicas -", sheet_name)
                    curr_sheet["headers"] = headers
                    curr_sheet["data_rows"] = all_data
            new_validated_data[sheet_name] = curr_sheet

        print("current_sheets", current_sheets)
        result = {
            "structured_data": new_validated_data,
            "current_sheets": current_sheets,
        }
        return result, [], None

    def split_intermediary_file(self, task_params=None):
        params = {
            "file": self.file.name,
            "final_path": self.final_path,
        }

        return []


    def decompress_file_gz(self, task_params=None):
        from task.serverless import async_in_lambda
        from inai.models import set_upload_path

        only_name = "split/NEW_FILE_NAME"
        directory = set_upload_path(self, only_name)

        params = {
            # "final_path": self.final_path,
            "file": self.file.name,
            "directory": directory,
        }
        task_params = task_params or {}
        # task_params[]
        print("task_params", task_params)
        task_params["models"] = [self]
        # task_params["function_after"] = "decompress_gz_after"

        new_task = async_in_lambda("decompress_gz", params, task_params)
        return new_task, [], self

    def get_data_from_excel(
            self, type_explor, file_control=None, task_params=None):
        from task.serverless import async_in_lambda
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
            }
            task_params = task_params or {}
            new_task = async_in_lambda("xls_to_csv", params, task_params)
            return (all_sheets, [], []), new_task
            # else:
            #     return (all_sheets, sheet_names, []), None

        include_names, exclude_names, include_idx, exclude_idx = explore_sheets(
            file_control)
        # print("include_names", include_names)
        # print("exclude_names", exclude_names)
        # print("include_idx", include_idx)
        # print("exclude_idx", exclude_idx)

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
            # print("SE TUVO QUE LEER EL EXCEL DE NUEVO")
            pending_sheets.append(sheet_name)
            continue
        # print("SÍ LLEGAMOS A VOLVER A CALCULAR LAS PESTAÑAS", filtered_sheets)
        return (all_sheets, filtered_sheets, []), None

    def decompress_gz_after(self, parent_task=None, **kwargs):
        from respond.models import SheetFile
        # import pathlib
        new_files = kwargs.get("new_files", {})
        # final_path = kwargs.get("final_path", {})
        # suffixes = pathlib.Path(final_path).suffixes
        generic_sample = {
            "all_data": kwargs.pop("all_data", []),
            "tail_data": kwargs.pop("tail_data", []),
        }
        for sheet_file in new_files:
            final_path = sheet_file.pop("final_path")
            total_rows = sheet_file.pop("total_rows")
            sheet_name = sheet_file.pop("sheet_name")
            SheetFile.objects.get_or_create(
                data_file=self,
                file=final_path,
                file_type_id="split",
                # matched=True,
                sheet_name=sheet_name,
                total_rows=total_rows,
                sample_data=generic_sample,
            )
        decode = kwargs.get("decode")
        if decode:
            file_control = self.petition_file_control.file_control
            if not file_control.decode and file_control.data_group.name != 'orphan':
                file_control.decode = decode
                file_control.save()
        return [], [], self

    def build_sample_data_after(self, parent_task=None, **kwargs):
        from respond.models import SheetFile
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
                total_rows=total_rows
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
        from scripts.recipe_specials import special_issste

        errors = []
        is_explore = bool(type_explor)

        if type_explor == 'only_save' or type_explor == 'forced_save':
            params = {
                "file": self.file.name,
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
            return errors, [], [], async_task

        all_sheets = self.all_sample_data
        # print("all_sheets", all_sheets)
        if is_explore and isinstance(all_sheets, dict):
            if "all_data" in all_sheets.get("default", {}):
                return all_sheets, ['default'], errors, None
            # print("keys", all_sheets.keys())

            all_keys = list(all_sheets.keys())
            first_sheet = all_keys[0]
            if "all_data" in all_sheets.get(first_sheet, {}):
                return all_sheets, all_keys, errors, None

        print("ESTOY EN UN LUGAR QUE NO DEBERÍA DE ESTAR CSV")
        raise Exception("ESTOY EN UN LUGAR QUE NO DEBERÍA DE ESTAR CSV")
