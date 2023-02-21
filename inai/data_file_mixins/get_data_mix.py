raws = {}


def execute_matches(row, file):
    from formula.models import MissingRow
    delegation = None
    missing_row = None
    if not state:
        columns_state = columns.filter(final_field__collection='State')
        if columns_state.exists():
            state = state_match(row, columns_state, 'State')
    # Delegación
    columns_deleg = columns.filter(final_field__collection='Delegation')
    if columns_deleg.exists():
        delegation = delegation_match(row, columns_state, 'Delegation')
        if not delegation:
            # missing_row = MissingRow.objects.get_or_create(file=file)
            missing_row = MissingRow.objects.create(
                file=file, row_seq=row[0], orinal_data=row)
        if delegation and not state:
            state = delegation.state
    recipe_row = []
    if not state:
        pass


class ExtractorsMix:
    petition_file_control: None
    save_errors: classmethod
    final_path: str

    def get_sample_data(self, task_params=None, **kwargs):
        from task.models import AsyncTask
        data_file = self
        all_tasks = kwargs.get("all_tasks", [])
        all_errors = kwargs.get("all_errors", [])
        task_params = task_params or {}
        data_file.error_process = []
        parent_task = task_params.get("parent_task")
        # previos_tasks
        AsyncTask.objects.filter(data_file=data_file)\
            .exclude(parent_task=parent_task)\
            .exclude(id=parent_task.id)\
            .update(is_current=False)
        data_file.save()
        task_params["models"] = [data_file]
        if not data_file.suffix:
            (data_file, errors, suffix), first_task = data_file.decompress_file(
                task_params=task_params)
            if data_file and suffix:
                data_file.suffix = suffix
                data_file.save()
            else:
                return [first_task], errors, None
                # else:
                #     all_results["ValidFormat"] = {
                #         "success": False,
                #         "errors": errors}
                # return all_tasks, errors, None
        new_errors = []
        if not data_file:
            print("______data_file:\n", data_file, "\n", "errors:", errors, "\n")
        elif not data_file.sample_data:
            task_params["function_after"] = kwargs.get("after_if_empty")
            current_file_ctrl = kwargs.get("current_file_ctrl")
            params_after = task_params.get("params_after", {})
            after_params_if_empty = kwargs.get("after_params_if_empty", {})
            params_after.update(after_params_if_empty)
            task_params["params_after"] = params_after
            data_file, new_errors, new_task = data_file.transform_file_in_data(
                'only_save', file_control=current_file_ctrl,
                task_params=task_params)
            if new_task:
                all_tasks.append(new_task)
                return all_tasks, all_errors, None
        if new_errors:
            all_errors.extend(new_errors)
            return all_tasks, all_errors, None
        return all_tasks, all_errors, data_file

    def transform_file_in_data(
            self, type_explor, file_control=None, task_params=None):
        from category.models import FileFormat
        is_explore = bool(type_explor)
        data_file = self
        # is_auto = type_explor == 'auto_explore'
        status_error = 'explore_fail' if is_explore else 'extraction_failed'
        if not file_control:
            file_control = data_file.petition_file_control.file_control
        is_orphan = file_control.data_group.name == "orphan"
        new_task = None
        current_sheets = ["default"]
        same_suffix = True
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

        if is_explore:
            data_file.sample_data = validated_data
            data_file.save()

        if type_explor == 'only_save':
            return data_file, errors, new_task

        row_headers = file_control.row_headers or 0
        # for sheet_name, all_data in validated_data.items():
        new_validated_data = {}
        for sheet_name in current_sheets:
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
                    nulls = [header for header in headers[1:] if not header]
                    few_nulls = len(nulls) < 2
                    if not few_nulls and len(all_data) > row_headers:
                        plus_rows = 1
                        headers = all_data[row_headers]
                        nulls = [header for header in headers[1:] if not header]
                        # if nulls:
                        #    continue
                    few_nulls = len(nulls) < 2
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
                    print("No pasó las pruebas básicas")
                    curr_sheet["headers"] = headers
                    curr_sheet["data_rows"] = all_data
                    pendiente_hasta_aca = 0
            new_validated_data[sheet_name] = curr_sheet

        # if not is_explore:
        #     matched_rows = []
        #     for row in validated_rows:
        #         row = execute_matches(row, self)
        #         matched_rows.append(row)
        #     return matched_rows

        result = {
            "structured_data": new_validated_data,
            "current_sheets": current_sheets,
        }
        return result, [], None

    def get_data_from_excel(
            self, type_explor, file_control=None, task_params=None):
        from inai.models import Transformation
        from task.serverless import async_in_lambda
        from scripts.common import get_excel_file
        is_explore = bool(type_explor)
        if is_explore:
            all_sheets = self.sample_data or {}
        else:
            all_sheets = {}

        sheet_names = self.sheet_names or []
        has_sheet_names = bool(sheet_names)
        # if not sheet_names:
        #     try:
        #         print(self.final_path)
        #         excel_file = get_excel_file(self.final_path)
        #         sheet_names = excel_file.sheet_names
        #         self.sheet_names = sheet_names
        #         self.save()
        #     except Exception as error:
        #         import traceback
        #         print("obteniendo sheets", error)
        #         error_ = traceback.format_exc()
        #         return (None, None, [error_]), None
        if type_explor == 'only_save':
            # nrows = 220 if is_explore else None
            n_rows = 220 if len(sheet_names) < 10 else 40
            n_end = 30 if len(sheet_names) < 10 else 15
            saved_sheet_names = all_sheets.keys()
            pending_sheets = list(set(sheet_names) - set(saved_sheet_names))
            if pending_sheets or has_sheet_names:
                params = {
                    "final_path": self.final_path,
                    "n_rows": n_rows,
                    "n_end": n_end,
                    "sheets": pending_sheets,
                    "ready_sheets": saved_sheet_names,
                }
                task_params = task_params or {}
                params_after = task_params.get("params_after", {})
                params_after["current_sheets"] = pending_sheets
                task_params["params_after"] = params_after
                new_task = async_in_lambda(
                    "explore_data_xls", params, task_params)
                # if "errorMessage" in new_sheets:
                #     return None, None, [new_sheets["errorMessage"]]
                # all_sheets.update(new_sheets)
                return (all_sheets, [], []), new_task
            else:
                return (all_sheets, sheet_names, []), None

        file_transformations = Transformation.objects.filter(
            file_control=file_control,
            clean_function__name__icontains="_tabs_").prefetch_related(
            "clean_function")
        include_names = exclude_names = include_idx = exclude_idx = None
        current_sheets = []
        pending_sheets = []

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

        for position, sheet_name in enumerate(sheet_names, start=1):
            if include_names and sheet_name not in include_names:
                continue
            if exclude_names and sheet_name in exclude_names:
                continue
            if include_idx and position not in include_idx:
                continue
            if exclude_idx and position in exclude_idx:
                continue
            current_sheets.append(sheet_name)
            # xls.parse(sheet_name)
            if is_explore and sheet_name in all_sheets:
                if "all_data" in all_sheets[sheet_name]:
                    continue
            print("SE TUVO QUE LEER EL EXCEL DE NUEVO")
            pending_sheets.append(sheet_name)
            continue
        return (all_sheets, current_sheets, []), None

    def explore_data_xls_after(self, parent_task=None, **kwargs):
        # params_after = {}
        # if parent_task:
        #     params_after = parent_task.params_after
        new_sheets = kwargs.get("new_sheets", {})
        all_sheet_names = kwargs.get("all_sheet_names", [])
        self.sheet_names = all_sheet_names
        # current_sheets = params_after.get("current_sheets", [])
        # print(current_sheets)
        sample_data = self.sample_data or {}
        sample_data.update(new_sheets)
        self.sample_data = sample_data
        self.save()
        return [], [], self

    def get_data_from_file_simple(
            self, type_explor, file_control=None, task_params=None):
        from scripts.common import get_file, start_session
        from task.serverless import async_in_lambda
        from scripts.common import build_s3

        errors = []
        is_explore = bool(type_explor)

        if is_explore and isinstance(self.sample_data, dict):
            if "all_data" in self.sample_data.get("default", {}):
                return self.sample_data, errors, None
        if type_explor == 'only_save':
            params = {
                "file": self.file.name,
                "s3": build_s3(),
                "delimiter": file_control.delimiter or "|",
            }
            task_params = task_params or {}
            # params_after = task_params.get("params_after", {})
            # params_after["next_"] = is_explore
            # task_params["params_after"] = params_after
            function_after = task_params.get(
                "function_after", "find_matches_in_file_controls")
            task_params["function_after"] = function_after
            async_task = async_in_lambda(
                "explore_data_simple", params, task_params)
            return None, [], async_task

        s3_client, dev_resource = start_session()
        data = get_file(self, dev_resource)
        if isinstance(data, dict):
            if data.get("errors", False):
                return False, data["errors"], None
        data_rows = data.readlines()
        total_rows = len(data_rows)
        if is_explore:
            data_rows = data_rows[220]
        validated_data_default = self.divide_rows(
            data_rows, file_control, is_explore=is_explore)
        validated_data = {
            "default": {
                "all_data": validated_data_default[:200],
                "total_rows": total_rows,
            }
        }

        # is_issste = self.petition_file_control.petition.entity.institution.code == 'ISSSTE'
        # file_control = self.petition_file_control.file_control
        # if "|" in data[:5000]:
        #     file_control.delimiter = '|'
        # elif "," in data[:5000]:
        #     file_control.delimiter = ','
        #     if is_issste:
        #         data = special_coma(data)
        #         if ",,," in data[:5000]:
        #             data = special_excel(data)
        # #elif not set([',', '|']).issubset(data[:5000]):
        # else:
        #     return False, ['El documento está vacío']
        # file_control.save()
        # if is_issste:
        #     data = clean_special(data)
        # return data, [], None
        return validated_data, None, None

    def divide_rows(self, data_rows, file_control, is_explore=False):
        global raws
        from inai.models import NameColumn
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
