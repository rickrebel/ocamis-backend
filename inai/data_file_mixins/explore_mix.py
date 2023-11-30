
class ExploreMix:
    final_path: str
    petition_file_control: None

    # Guardado en funciones
    def get_sample_data(self, task_params=None, **kwargs):
        # from task.models import AsyncTask
        from django.utils import timezone
        from category.models import FileFormat
        from inai.models import SheetFile
        data_file = self
        task_params = task_params or {}
        data_file.error_process = []
        data_file.warning = []
        # parent_task = task_params.get("parent_task")
        # # previous_tasks
        # previous_tasks = AsyncTask.objects\
        #     .filter(data_file=data_file)\
        #     .exclude(parent_task=parent_task)\
        #     .exclude(id=parent_task.id)
        # for task in previous_tasks:
        #     task.is_current = False
        #     task.save()
        data_file.save()
        task_params["models"] = [data_file]
        if not data_file.suffix:
            (data_file, errors, suffix), first_task = data_file.decompress_file(
                task_params=task_params, **kwargs)
            if data_file and suffix:
                data_file.suffix = suffix
                data_file.save()
            elif first_task:
                return [first_task], errors, self
            else:
                self.save_errors(errors, 'explore|with_errors')
                return [], errors, self
        forced_save = kwargs.get("forced_save", False)
        sheet_names = data_file.sheet_names_list
        if not sheet_names:
            xls_format = FileFormat.objects.get(short_name="xls")
            if data_file.suffix in xls_format.suffixes:
                forced_save = True
            elif not data_file.sample_data:
                forced_save = True
            else:
                sample_data = data_file.sample_data or {}
                default_sheet = sample_data.get("default", {})
                previous_explore = default_sheet and \
                                   data_file.status_process.order > 6
                if previous_explore and default_sheet.get("tail_data"):
                    total_rows = default_sheet.pop("total_rows", 0)
                    SheetFile.objects.create(
                        file=data_file.file,
                        data_file=data_file,
                        sheet_name="default",
                        file_type_id="clone",
                        matched=True,
                        sample_data=default_sheet,
                        total_rows=total_rows
                    )
                    data_file.filtered_sheets = ["default"]
                    data_file.save()
                    sheet_names = ["default"]
                else:
                    forced_save = True
        new_errors = []
        # if not data_file.sample_data or forced_save:
        if forced_save:
            # print("NO HAY SAMPLE DATA O NO HAY SHEET NAMES")
            task_params["function_after"] = kwargs.get("after_if_empty")
            current_file_ctrl = kwargs.get("current_file_ctrl")
            params_after = task_params.get("params_after", {})
            after_params_if_empty = kwargs.get("after_params_if_empty", {})
            params_after.update(after_params_if_empty)
            task_params["params_after"] = params_after
            if forced_save or not sheet_names:
                type_explor = 'forced_save'
            else:
                type_explor = 'only_save'
            data_file, new_errors, new_task = data_file.transform_file_in_data(
                type_explor, file_control=current_file_ctrl,
                task_params=task_params)
            if new_task:
                return [new_task], new_errors, data_file
        if new_errors:
            self.save_errors(new_errors, 'explore|with_errors')
            return [], new_errors, data_file
        return [], [], data_file

    def transform_data(self, task_params, **kwargs):
        from inai.data_file_mixins.matches_mix import Match
        my_match = Match(self, task_params)
        return my_match.build_csv_converted(is_prepare=False)

    def prepare_transform(self, task_params, **kwargs):
        from inai.data_file_mixins.matches_mix import Match
        data_file = self.count_file_rows()
        my_match = Match(data_file, task_params)
        return my_match.build_csv_converted(is_prepare=True)

    def insert_data(self, task_params, **kwargs):
        from inai.data_file_mixins.insert_mix import Insert
        from inai.models import LapSheet
        raise "Esta función ya no se usa"

    def count_file_rows(self):
        from inai.models import SheetFile
        from django.db.models import Sum
        file_control = self.petition_file_control.file_control
        minus_headers = file_control.row_start_data - 1
        total_count_query = SheetFile.objects.filter(
            data_file=self,
            sheet_name__in=self.filtered_sheets
        ).aggregate(Sum("total_rows"))
        total_count = total_count_query.get("total_rows__sum", 0)
        minus_headers = len(self.filtered_sheets) * minus_headers
        total_count -= minus_headers
        self.total_rows = total_count
        self.save()
        return self

    def find_coincidences_from_aws(self, task_params=None, **kwargs):
        data_file, kwargs = self.corroborate_save_data(task_params, **kwargs)
        data_file, saved, errors = data_file.find_coincidences(saved=False)
        if not saved and not errors:
            errors = ["No coincide con el formato del archivo 3"]
        if errors:
            data_file.save_errors(errors, "explore|with_errors")
            return [], errors, None
        elif data_file.stage_id == 'cluster':
            data_file.finished_stage("cluster|finished")
        return [], errors, None

    def find_and_counting_from_aws(self, task_params=None, **kwargs):
        n_t, errors, data_file = self.find_coincidences_from_aws(
            task_params=task_params, **kwargs)
        if errors:
            return [], errors, None
        return [], errors, None

    def verify_coincidences(self, task_params, **kwargs):
        data_file = self
        data_file, saved, new_errors = data_file.find_coincidences()
        if not saved and not new_errors:
            new_errors = ["No coincide con el grupo de control (4)"]
        return [], new_errors, data_file

    def has_exact_matches(self, filtered_sheets=None):
        # print("filtered_sheets", filtered_sheets)
        if not filtered_sheets or not self.sheet_files.exists():
            return False
        sheets_matched = self.sheet_files.filter(matched=True)\
            .values_list("sheet_name", flat=True).distinct()
        # print("sheets_matched", sheets_matched)
        if not sheets_matched.exists():
            return False
        set_sheets_matched = set(sheets_matched)
        set_filtered_sheets = set(filtered_sheets)
        # print("set_filtered_sheets", set_filtered_sheets)
        # print("set_sheets_matched", set_sheets_matched)
        return set_filtered_sheets.issubset(set_sheets_matched)

    def find_coincidences(
            self, saved=False, petition=None, file_ctrl=None,
            task_params=None, **kwargs):
        from inai.models import PetitionFileControl, DataFile
        from data_param.models import NameColumn
        from scripts.common import similar
        data_file = self
        already_cluster = not bool(file_ctrl)
        data, errors, new_task = data_file.transform_file_in_data(
            'auto_explore', task_params=task_params, file_control=file_ctrl)
        if not petition or not file_ctrl:
            pfc = data_file.petition_file_control
            if not petition:
                petition = pfc.petition
            if not file_ctrl:
                file_ctrl = pfc.file_control
        if errors:
            return data_file, saved, errors
        if not data and not errors and not new_task:
            return data_file, saved, errors
        # print("data", data)
        current_sheets = data["current_sheets"]
        structured_data = data["structured_data"]
        if already_cluster:
            # print("INTENTO GUARDAR current_sheets", current_sheets)
            data_file.filtered_sheets = current_sheets
            data_file.save()
        is_match_ready = data_file.has_exact_matches(current_sheets)
        if is_match_ready:
            return data_file, True, []
        # is_orphan = file_ctrl.data_group.name == "orphan"
        all_data_files = {}
        same_data_files = DataFile.objects\
            .filter(file=self.file)\
            .exclude(petition_file_control__file_control__data_group__name="orphan")
        for df in same_data_files:
            all_data_files[df.petition_file_control_id] = df
        name_columns_simple = NameColumn.objects.filter(
            file_control=file_ctrl, position_in_data__isnull=False)
        sorted_sheet_names = current_sheets.copy()
        other_sheets = [sheet for sheet in structured_data.keys()
                        if sheet not in sorted_sheet_names]
        sorted_sheet_names.extend(other_sheets)
        current_pfc = data_file.petition_file_control_id
        only_cols_with_headers = file_ctrl.file_transformations\
            .filter(clean_function__name="only_cols_with_headers").exists()
        sheets_matched_ids = []

        for sheet_name in sorted_sheet_names:
            # headers = validated_rows[row_headers-1] if row_headers else []
            if not structured_data[sheet_name].get("headers"):
                if not file_ctrl.row_headers:
                    try:
                        total_cols = len(structured_data[sheet_name]["all_data"][0])
                        if total_cols == len(name_columns_simple):
                            same_headers = True
                        else:
                            continue
                    except Exception as e:
                        print("error intentando obtener headers", e)
                        continue
                else:
                    continue
            else:
                name_columns = name_columns_simple \
                    .values_list("name_in_data", flat=True)
                headers = structured_data[sheet_name]["headers"]
                headers = [head.strip().upper() for head in headers]
                if only_cols_with_headers:
                    headers = [head for head in headers if head]
                name_columns_list = [
                    name.strip().upper() for name in list(name_columns)]
                print("name_columns_list", name_columns_list)
                print("headers", headers, "\n")
                same_headers = name_columns_list == headers
                print("same_headers", same_headers)
                if not same_headers:
                    total_cols = len(structured_data[sheet_name]["all_data"][0])
                    if total_cols != len(name_columns_simple):
                        continue
                    coincidences = 0
                    need_save = []
                    for (idx, name_col) in enumerate(name_columns_simple):
                        name_upper = name_col.name_in_data.strip().upper()
                        if name_upper == headers[idx]:
                            coincidences += 1
                            continue
                        if name_col.alternative_names:
                            if headers[idx] in name_col.alternative_names:
                                coincidences += 1
                                continue
                        if not already_cluster:
                            continue
                        if not name_upper or not name_upper:
                            coincidences += 1
                            continue
                        if similar(name_upper, headers[idx]) > 0.8:
                            alt_names = name_col.alternative_names or []
                            name_col.alternative_names = alt_names + [headers[idx]]
                            need_save.append(name_col)
                            coincidences += 1
                    if coincidences + 1 >= len(name_columns_simple):
                        same_headers = True
                        for name_col in need_save:
                            name_col.save()

            if not same_headers:
                continue

            def save_sheet_file(d_f=data_file, save_sample_data=False):
                from inai.models import SheetFile

                try:
                    sheet_f = d_f.sheet_files\
                        .filter(sheet_name=sheet_name).first()
                    if not sheet_f:
                        original_sheet_f = data_file.sheet_files\
                            .filter(sheet_name=sheet_name).first()
                        sheet_f = SheetFile.objects.create(
                            data_file=d_f,
                            sheet_name=sheet_name,
                            total_rows=original_sheet_f.total_rows,
                            sample_data=original_sheet_f.sample_data)
                    if save_sample_data:
                        sheet_f.sample_data = structured_data[sheet_name]
                    sheet_f.matched = True
                    sheet_f.save()
                    sheets_matched_ids.append(sheet_f.id)
                except Exception as e:
                    raise Exception(f"No se encontró el archivo con el "
                                    f"nombre de hoja {sheet_name} \n {e}")

            if sheet_name not in current_sheets:
                if data_file.petition_file_control_id in all_data_files:
                    save_sheet_file(data_file)
                    data_file.add_warning(
                        "Hay pestañas con el mismo formato, no incluidas en "
                        "por los filtros de inclusión y exclusión")
                continue
            try:
                succ_pet_file_ctrl, created_pfc = PetitionFileControl.objects \
                    .get_or_create(
                        file_control=file_ctrl, petition=petition)
            except PetitionFileControl.MultipleObjectsReturned:
                errors = ["El grupos de control está duplicado en la solicitud"]
                return data_file, saved, errors
            # validated_data[sheet_name] = structured_data[sheet_name]
            current_pfc = succ_pet_file_ctrl.id
            already_in_pfc = current_pfc in all_data_files
            # if pet_file_saved:
            #     continue
            if all_data_files and not already_in_pfc:
                original_sheet_files = data_file.sheet_files.all()
                info_text = "El archivo está en varios grupos de control"
                data_file.add_warning(info_text)
                new_data_file = data_file
                new_data_file.pk = None
                new_data_file.petition_file_control = succ_pet_file_ctrl
                new_data_file.filtered_sheets = current_sheets
                # new_data_file.change_status("explore|finished")
                new_data_file.finished_stage('explore|finished')
                # new_data_file.sample_data = validated_data
                new_data_file.save()
                new_data_file.add_warning(info_text)
                all_data_files[current_pfc] = new_data_file
                for sheet_file in original_sheet_files:
                    sheet_file.pk = None
                    sheet_file.data_file = new_data_file
                    if sheet_file.sheet_name == sheet_name:
                        sheet_file.sample_data = structured_data[sheet_name]
                        sheet_file.matched = True
                    elif sheet_file.matched == None:
                        sheet_file.matched = False
                    sheet_file.save()
            else:
                current_file = all_data_files.get(current_pfc, data_file)
                # current_file.sample_data = validated_data
                save_sheet_file(current_file, True)
                if not saved and not already_cluster:
                    current_file.filtered_sheets = current_sheets
                saved = True
                if not already_in_pfc:
                    current_file.petition_file_control = succ_pet_file_ctrl
                    # current_file = current_file.change_status("explore|finished")
                    current_file.stage_id = "explore"
                    current_file.status_id = "finished"
                current_file.save()
                all_data_files[current_pfc] = current_file
        if current_pfc in all_data_files:
            data_file.sheet_files.exclude(id__in=sheets_matched_ids)\
                                 .update(matched=False)
            is_match_ready = data_file.has_exact_matches(current_sheets)
            print("is_match_ready", is_match_ready)
            if not is_match_ready:
                errors = ["No todas las pestañas filtradas coinciden con "
                          "el grupo de control"]
                return data_file, saved, errors
            return all_data_files[current_pfc], saved, []
        return data_file, saved, []
        #return all_data_files, saved, []

    def decompress_file(self, task_params=None, **kwargs):
        import pathlib
        from category.models import FileFormat
        import re
        #Se obienen todos los tipos del archivo inicial:
        # print("final_path: ", self.final_path)
        suffixes = pathlib.Path(self.final_path).suffixes
        re_is_suffix = re.compile(r'^\.([a-zA-Z]{3,4})$')
        suffixes = [suffix.lower() for suffix in suffixes
                    if bool(re.search(re_is_suffix, suffix)) or suffix == '.gz']
        # print("suffixes", suffixes)
        errors = []
        main_error = None
        new_task = None
        data_file = None
        task_params["function_after"] = "decompress_gz_after"
        if '.gz' in suffixes:
            if not self.sheet_files.exists():
                new_task, errors, data_file = self.decompress_file_gz(
                    task_params=task_params)
                main_error = "descomprimir el archivo gz"
            suffixes.remove('.gz')
        elif '.zip' in suffixes or '.rar' in suffixes:
            errors = ["Mover a 'archivos no finales' para descomprimir desde allí"]
        elif (len(suffixes) == 1 and
              not self.sheet_files.filter(file_type_id='split').exists()):
            file_size = self.file.size
            if file_size > 400000000:
                real_suffix = suffixes[0]
                xls_format = FileFormat.objects.get(short_name="xls")
                if real_suffix not in xls_format.suffixes:
                    new_task, errors, data_file = self.decompress_file_gz(
                        task_params=task_params)
                    main_error = "dividir el archivo gigante"
        if errors or new_task:
            if errors and main_error:
                errors = [f"No se pudo {main_error}: {self.final_path}"]
            return (data_file, errors, None), new_task

        # Obtener el tamaño
        # file_name = self.file_name
        real_suffixes = suffixes
        if len(real_suffixes) != 1:
            errors = [("Tiene más o menos extensiones de las que"
                       " podemos reconocer: %s" % real_suffixes)]
            return (None, errors, None), None
        real_suffixes = set(real_suffixes)
        readable_suffixes = FileFormat.objects.filter(readable=True)\
            .values_list("suffixes", flat=True)
        final_readeable = []
        for suffix in list(readable_suffixes):
            final_readeable += suffix
        # final_readeable = [suffix for suffix in list(readable_suffixes)]

        if not real_suffixes.issubset(final_readeable):
            errors = ["Formato no legible", "%s" % suffixes]
            return (None, errors, None), None
        # print("Parece que todo está bien")
        return (self, [], list(real_suffixes)[0]), None

    def corroborate_save_data(self, task_params=None, **kwargs):
        from_aws = kwargs.get("from_aws", False)
        print("from_aws", from_aws)

        if from_aws:
            x, y, data_file = self.build_sample_data_after(**kwargs)
            parent_task = task_params.get("parent_task", None)
            if parent_task.params_after:
                kwargs.update(parent_task.params_after)
        else:
            data_file = self
        return data_file, kwargs

    def find_matches_in_file_controls(self, task_params=None, **kwargs):
        from data_param.models import FileControl
        data_file, kwargs = self.corroborate_save_data(task_params, **kwargs)
        saved = False
        all_errors = []
        all_file_controls = kwargs.get("all_file_controls", None)
        if not all_file_controls:
            all_file_controls_ids = kwargs.get("all_file_controls_ids", [])
            all_file_controls = FileControl.objects.filter(
                id__in=all_file_controls_ids)
        for file_ctrl in all_file_controls:
            if data_file.suffix not in file_ctrl.file_format.suffixes:
                continue
            data_file, saved, errors = data_file.find_coincidences(
                saved, file_ctrl=file_ctrl)
            if errors:
                all_errors.extend(errors)
        if not saved:
            all_errors.append("No existe ningún grupo de control coincidente")
            data_file.save_errors(all_errors, "explore|with_errors")
        return None, all_errors, None

    def build_complex_headers(self, task_params=None, **kwargs):
        from data_param.models import NameColumn

        data_file = self
        all_errors = []
        data, errors, new_task = data_file.transform_file_in_data(
            'auto_explore', task_params=task_params)
        if errors:
            all_errors.extend(errors)
            data_file.save_errors(all_errors, "explore|with_errors")
            return None, errors, None

        def text_normalizer(text):
            import re
            import unidecode
            final_text = text.upper().strip()
            final_text = unidecode.unidecode(final_text)
            final_text = re.sub(r'[^A-Z][DE|DEL][^A-Z]', ' ', final_text)
            final_text = re.sub(r' +', ' ', final_text)
            final_text = re.sub(r'[^A-Z]', '', final_text)
            final_text = final_text.strip()
            return final_text

        valid_fields = [
            "name_in_data", "column_type", "final_field",
            "final_field__parameter_group", "data_type"]
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
            file_control = data_file.petition_file_control.file_control
            data_groups = [file_control.data_group.name, 'catalogs']
            # print(data_groups)
            all_name_columns = NameColumn.objects.filter(
                final_field__isnull=False,
                name_in_data__isnull=False,
                final_field__parameter_group__data_group__name__in=data_groups,
            ).values(*valid_fields)

            final_names = {}
            for name_col in all_name_columns:
                standard_name = text_normalizer(name_col["name_in_data"])
                unique_name = (
                    f'{standard_name}-{name_col["final_field"]}-'
                    f'{name_col["final_field__parameter_group"]}')
                if final_names.get(standard_name, False):
                    if not final_names[standard_name]["valid"]:
                        continue
                    elif final_names[standard_name]["unique_name"] != unique_name:
                        final_names[standard_name]["valid"] = False
                    continue
                else:
                    base_dict = {
                        "valid": True,
                        "unique_name": unique_name,
                        "standard_name": standard_name,
                    }
                    base_dict.update(name_col)
                    final_names[standard_name] = base_dict
            final_names = {
                name: vals for name, vals in final_names.items()
                if vals["valid"] }
            for (position, header) in enumerate(headers, start=1):
                std_header = text_normalizer(header)
                base_dict = { "position_in_data": position }
                if final_names.get(std_header, False):
                    vals = final_names[std_header]
                    base_dict.update({ field: vals[field] for field in valid_fields })
                base_dict["name_in_data"] = header
                complex_headers.append(base_dict)
            first_valid_sheet["complex_headers"] = complex_headers
        except Exception as e:
            print("HUBO UN ERRORZASO")
            print(e)
        # print(data["structured_data"][:6])
        return None, None, first_valid_sheet
