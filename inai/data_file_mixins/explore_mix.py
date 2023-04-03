
class ExploreMix:
    final_path: str
    petition_file_control: None

    def get_sample_data(self, task_params=None, **kwargs):
        # from task.models import AsyncTask
        from django.utils import timezone
        from category.models import FileFormat
        from inai.models import SheetFile
        # print("get_sample_data 1", timezone.now())
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
        # print("get_sample_data 2", timezone.now())
        if not data_file.suffix:
            (data_file, errors, suffix), first_task = data_file.decompress_file(
                task_params=task_params)
            if data_file and suffix:
                data_file.suffix = suffix
                data_file.save()
            else:
                self.save_errors(errors, 'explore|with_errors')
                return [first_task], errors, None
        # print("get_sample_data 3", timezone.now())
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
        # print("get_sample_data 4", timezone.now())
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
                return [new_task], new_errors, None
        # print("get_sample_data 5", timezone.now())
        if new_errors:
            self.save_errors(new_errors, 'explore|with_errors')
            return [], new_errors, None
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
        # if file_format.short_name == 'csv' or file_format.short_name == 'txt':
        #     total_count = self.sample_data["default"]["total_rows"]
        # elif file_format.short_name == 'xls':
        #     total_count = self.count_xls_rows()
        #     minus_headers = len(self.sample_data.keys()) * minus_headers
        total_count -= minus_headers
        self.total_rows = total_count
        self.save()
        return self
        # self.change_status("success_counting")
        # return {"total_rows": total_count}

    # RICK 19: Según yo, esto ya no debería existir
    def count_csv_rows(self):
        from scripts.common import get_file, start_session
        s3_client, dev_resource = start_session()
        data = get_file(self, dev_resource)
        final_count = len(data.readlines())
        return final_count

    # RICK 19: Según yo, esto ya no debería existir
    def count_xls_rows(self):
        from scripts.common import build_s3
        from task.serverless import count_excel_rows
        total_count = 0
        sample_data = self.sample_data
        explore_modificated = False

        if isinstance(sample_data, dict):
            current_sheets = sample_data.keys()
            sheets_for_count = []
            for sheet_name in current_sheets:
                if "total_rows" in sample_data[sheet_name]:
                    total_count += sample_data[sheet_name]["total_rows"]
                else:
                    sheets_for_count.append(sheet_name)
                    #excel_file = pd.ExcelFile(self.file, sheet_name=sheet_name)
            params = {
                "sheets": sheets_for_count,
                "file": self.file.name,
                's3': build_s3(),
            }
            all_counts = count_excel_rows(params)
            # print("all_counts", all_counts)
            for sheet_name in current_sheets:
                if sheet_name in all_counts:
                    sample_data[sheet_name]["total_rows"] = all_counts[sheet_name]
                    total_count += all_counts[sheet_name]
                    explore_modificated = True
        if explore_modificated:
            self.sample_data = sample_data
            self.save()
        return total_count

    def find_coincidences_from_aws(self, task_params=None, **kwargs):
        data_file, kwargs = self.corroborate_save_data(task_params, **kwargs)
        data_file, saved, errors = data_file.find_coincidences(saved=False)
        if not saved and not errors:
            errors = ["No coincide con el formato del archivo 3"]
        if errors:
            data_file.save_errors(errors, "explore|with_errors")
            return [], errors, None
        elif data_file.stage_id == 'cluster':
            data_file.change_status("cluster|finished")
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
        if not filtered_sheets or not self.sheet_files.exists():
            return False
        sheets_matched = self.sheet_files.filter(matched=True)\
            .values_list("sheet_name", flat=True).distinct()
        if not sheets_matched.exists():
            return False
        set_sheets_matched = set(sheets_matched)
        set_filtered_sheets = set(filtered_sheets)
        return set_filtered_sheets.issubset(set_sheets_matched)

    def find_coincidences(
            self, saved=False, petition=None, file_ctrl=None,
            task_params=None, **kwargs):
        from inai.models import PetitionFileControl, DataFile
        from data_param.models import NameColumn
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
        current_sheets = data["current_sheets"]
        structured_data = data["structured_data"]
        if already_cluster:
            print("INTENTO GUARDAR current_sheets", current_sheets)
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
                same_headers = name_columns_list == headers

            def save_sheet_file(d_f=data_file, save_sample_data=False):
                table_s = d_f.sheet_files.filter(sheet_name=sheet_name).first()
                if table_s:
                    if save_sample_data:
                        table_s.sample_data = structured_data[sheet_name]
                    table_s.matched = True
                    table_s.save()
                else:
                    raise Exception(f"No se encontró el archivo con el "
                                    f"nombre de hoja {sheet_name}")

            if not same_headers:
                continue
            if sheet_name not in current_sheets:
                if data_file.petition_file_control_id in all_data_files:
                    save_sheet_file()
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
                new_data_file.change_status("explore|finished")
                # new_data_file.sample_data = validated_data
                new_data_file.save()
                new_data_file.add_warning(info_text)
                all_data_files[current_pfc] = new_data_file
                for sheet_file in original_sheet_files:
                    sheet_file.pk = None
                    sheet_file.data_file = new_data_file
                    if sheet_file.sheet_name == sheet_name:
                        sheet_file.sample_data = structured_data[sheet_name]
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
            is_match_ready = data_file.has_exact_matches(current_sheets)
            if not is_match_ready:
                errors = ["No todas las pestañas filtradas coinciden con "
                          "el grupo de control"]
                return data_file, saved, errors
            return all_data_files[current_pfc], saved, []
        return data_file, saved, []
        #return all_data_files, saved, []

    def decompress_file(self, task_params=None):
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
        all_errors = []
        if '.gz' in suffixes:
            #print("path", self.file.path)
            #print("name", self.file.name)
            #print("url", self.file.url)
            #Se llama a la función que descomprime el arhivo
            if not self.child_files.all().count():
                success_decompress, example_file = self.decompress_file_gz(
                    task_params=task_params)
                if not success_decompress:
                    print("error en success_decompress")
                    errors = ['No se pudo descomprimir el archivo gz %s' % self.final_path]
                    return (None, errors, None), None
                #Se vuelve a obtener la ubicación final del nuevo archivo
                #Como el archivo ya está descomprimido, se guarda sus status
            self = self.change_status('explore|finished')
            # Se realiza todito el proceso para guardar el nuevo objeto DataFinal,
            # manteniendo todas las características del archivo original
            suffixes.remove('.gz')
            # print("new_suffixex",  suffixes)
        elif '.zip' in suffixes:
            #[directory, only_name] = self.path.rsplit("/", 1)
            #[base_name, extension] = only_name.rsplit(".", 1)
            error_zip = "Mover a 'archivos no finales' para descomprimir desde allí"
            return (None, [error_zip], None), None

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

    def decompress_file_gz(self, task_params=None):
        print("decompress_file_gz")
        import gzip
        from inai.models import DataFile
        from category.models import StatusControl
        from scripts.common import start_session, create_file
        from django.conf import settings
        size_hint = 330 * 1000000
        initial_status = StatusControl.objects.get(
            name='initial', group="process")

        def write_split_files(complete_file, simple_name):
            [base_name, extension] = simple_name.rsplit(".", 1)
            file_num = 0
            last_file = None
            while True:
                buf = complete_file.readlines(size_hint)
                if not buf:
                    print("No hay más datos")
                    # we've read the entire file in, so we're done.
                    break
                file_num += 1
                curr_only_name = f"{base_name}_{file_num + 1}.{extension}"
                buf = b"".join(buf)
                current_s3_client, dev_resource_2 = start_session()
                print("rr_file_name", curr_only_name)
                rr_file_name, errors = create_file(
                    buf, current_s3_client, only_name=curr_only_name,
                    file_obj=self)
                print("exito en creación de archivo")
                print("errors", errors)
                DataFile.objects.create(
                    file=rr_file_name,
                    origin_file=self,
                    date=self.date,
                    status_process=initial_status,
                    # FALTA EL STATUS Y STAGE
                    #Revisar si lo más fácil es poner o no los siguientes:
                    #file_control=original_file.file_control,
                    petition_file_control=self.petition_file_control,
                    #petition=original_file.petition,
                    petition_month=self.petition_month)
            return True

        try:
            decompressed_path = self.file.name.replace(".gz", "")
            pos_slash = decompressed_path.rfind("/")
            only_name = decompressed_path[pos_slash + 1:]
            s3_client, dev_resource = start_session()
            bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
            gz_obj = dev_resource.Object(
                bucket_name=bucket_name,
                key=f"{settings.AWS_LOCATION}/{self.file.name}"
                )
            with gzip.GzipFile(fileobj=gz_obj.get()["Body"]) as gzip_file:
                #print(gzipfile.readlines(200))
                success_gz = write_split_files(gzip_file, only_name)
                return success_gz, None
                #content = gzipfile.read()
        except Exception as e:
            print("error", e)
            return False, e

    def split_file(self):
        from inai.models import DataFile
        from django.conf import settings
        from scripts.common import get_file, start_session, create_file

        #s3_client, dev_resource = start_session()
        #buffer = get_file(self, dev_resource)
        #[directory, only_name] = buffer.rsplit("/", 1)
        is_prod = getattr(settings, "IS_PRODUCTION", False)
        #print("final_path: ", self.final_path)
        [directory, only_name] = self.final_path.rsplit("\\", 1)
        [base_name, extension] = only_name.rsplit(".", 1)

        SIZE_HINT = 330 * 1000000

        original_file = self.origin_file or self

        def write_splited_files(complete_file):
            from category.models import StatusControl

            initial_status = StatusControl.objects.get(
                name='initial', group="process")
            file_num = 0
            while True:
                buf = complete_file.readlines(SIZE_HINT)
                if not buf:
                    # we've read the entire file in, so we're done.
                    break
                curr_only_name = f"{base_name}_{file_num + 1}.{extension}"
                print("buf_size", len(buf))
                if is_prod:
                    buf = "\n".join(buf)
                    rr_file_name, errors = create_file(
                        buf, s3_client, only_name=curr_only_name, file_obj=self)
                else:
                    rr_file_name = f"{directory}\\{curr_only_name}"
                    outFile = open(rr_file_name, "wt", encoding="UTF-8")
                    outFile.writelines(buf)
                    outFile.close()
                file_num += 1
                DataFile.objects.create(
                    file=rr_file_name,
                    #origin_file=original_file,
                    origin_file=self,
                    date=original_file.date,
                    # FALTA STATUS Y STAGE
                    status_process=initial_status,
                    #Revisar si lo más fácil es poner o no los siguientes:
                    #file_control=original_file.file_control,
                    petition_file_control=original_file.petition_file_control,
                    #petition=original_file.petition,
                    petition_month=original_file.petition_month)
            return file_num
        # RICK AWS corroborar esto:
        if is_prod:
            s3_client, dev_resource = start_session()
            complete_file = get_file(self, dev_resource)
            complete_file = complete_file.read()
            file_num = write_splited_files(complete_file)
        else:
            with open(self.final_path, "rt") as fl:
                file_num = write_splited_files(fl)
                fl.close()
            #os.remove(self.final_path)

        print("SE LOGRARON:", file_num)
        #print("directory", directory)
        #print("only_name", only_name)
        #print("base_name", base_name)
        #print("extension", extension)
        return file_num

    def corroborate_save_data(self, task_params=None, **kwargs):
        from_aws = kwargs.get("from_aws", False)
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

    #Comienzo del proceso de transformación.
    #Si es esploración (is_explore) solo va a obtener los headers y las
    #primeras filas
    # RICK 14
    def start_file_process(self, is_explore=False):
        from inai.models import DataFile
        from category.models import FileFormat
        #FieldFile.open(mode='rb')
        self.error_process = []
        self.save()
        #se llama a la función para descomprimir el archivo o archivos:
        childs_count = self.child_files.count()
        (new_self, errors, suffix), first_task = self.decompress_file()
        # print("new_self: ", new_self)
        if errors:
            status_error = 'explore|with_errors' if is_explore else 'transform|with_errors'
            self.save_errors(errors, status_error)
            return None, errors, None
        new_childs_count = self.child_files.count()
        count_splited = 0
        file_size = new_self.file.size
        if file_size > 400000000:
            if suffix in FileFormat.objects.get(short_name='xls').suffixes:
                errors = ["Archivo excel muy grande, aún no se puede partir"]
                return None, errors, None
            count_splited = new_self.split_file()
        if errors:
            status_error = 'explore|with_errors' if is_explore else 'transform|with_errors'
            new_self.save_errors(errors, status_error)
            return None, errors, None
        if count_splited and not is_explore:
            warnings = ["Son muchos archivos y tardarán en procesarse, espera por favor"]
            return None, warnings, None
        if not is_explore:
            new_self.build_catalogs()
            new_errors = []
            new_tasks = []
        elif count_splited:
            #FALTA AFINAR FUNCIÓN PARA ESTO
            new_errors = []
            new_tasks = []
            all_children = DataFile.objects.filter(origin_file=new_self)
            for ch_file in all_children:
                data, current_errors, new_task = ch_file.transform_file_in_data(
                    'is_explore')
                new_errors.extend(current_errors)
                new_tasks.append(new_task)
        elif new_childs_count and childs_count < new_childs_count:
            first_child = new_self.child_files.first()
            data, new_errors, new_task = first_child.transform_file_in_data(
                'is_explore')
            new_tasks = [new_task]
        else:
            data, new_errors, new_task = new_self.transform_file_in_data(
                'is_explore')
            new_tasks = [new_task]
        if is_explore:
            #print(data["headers"])
            #print(data["structured_data"][:6])
            return data, new_errors, new_tasks
        else:
            print("POR ALGUNA RAZÓN NO ES EXPLORE")
            return new_self, new_errors, new_tasks

    #RICK 19; corroborar que esto ya no e llame, está muy desfasado
    # def comprobate_coincidences(self, task_params=None, **kwargs):
    #     from inai.models import DataFile
    #     # print("new_children_ids: ", new_children_ids)
    #     data_file, kwargs = self.corroborate_save_data(task_params, **kwargs)
    #     from_aws = kwargs.get("from_aws", False)
    #
    #     file_ctrl = data_file.petition_file_control.file_control
    #     petition = data_file.petition_file_control.petition
    #
    #     parent_task = task_params.get("parent_task", None)
    #     if from_aws:
    #         new_children_ids = kwargs.get("new_children_ids", [])
    #         new_children = DataFile.objects.filter(id__in=new_children_ids)
    #     else:
    #         init_children = list(
    #             self.child_files.all().values_list('id', flat=True))
    #         # RICK 14
    #         (data_file, errors, suffix), first_task = self.decompress_file()
    #         if not data_file:
    #             print("______data_file:\n", data_file, "\n", "errors:", errors, "\n")
    #             return None, errors, 0
    #         new_children = data_file.child_files.all()
    #         if init_children:
    #             new_children = new_children.exclude(id__in=init_children)
    #         new_children_ids = new_children.values_list('id', flat=True)
    #
    #     task_params = task_params or {}
    #     params_after = task_params.get("params_after", { })
    #     params_after["new_children_ids"] = list(new_children_ids)
    #     # params_after["all_file_controls_ids"] = [file_ctrl.id]
    #     task_params["params_after"] = params_after
    #     task_params["function_after"] = "comprobate_coincidences"
    #     task_params["models"] = [data_file]
    #
    #     if not new_children_ids:
    #         data_file, errors, new_task = data_file.transform_file_in_data(
    #             'only_save', file_control=file_ctrl,
    #             task_params=task_params)
    #         if new_task:
    #             return data_file, errors, 0
    #         if not data_file:
    #             print("NO ENTIENDO QUÉ PASÓ")
    #             return None, errors, 0
    #         data_file, saved, errors = data_file.find_coincidences(
    #             False, petition=petition, file_ctrl=file_ctrl)
    #     else:
    #         print("HAY NUEVOS CHILDREN")
    #         first_child = new_children.first()
    #         first_child, errors, new_task = first_child.transform_file_in_data(
    #             'only_save', file_control=file_ctrl,
    #             task_params=task_params)
    #         if new_task:
    #             return first_child, errors, 0, new_task
    #         first_child, saved, errors = first_child.find_coincidences(
    #             False, petition=petition, file_ctrl=file_ctrl)
    #         if saved:
    #             for child in new_children:
    #                 child.sample_data = first_child.sample_data
    #                 child.status_process = first_child.status_process
    #                 child.save()
    #             data_file.sample_data = first_child.sample_data
    #             data_file.status_process = first_child.status_process
    #             data_file = data_file.save()
    #
    #     if not errors and not saved and file_ctrl.row_headers:
    #         errors.append("Las columnas no coincide con el archivo")
    #         # errors = ["No hay coincidencias con las columnas"]
    #     if errors:
    #         data_file = data_file.save_errors(errors, "explore_fail")
    #         return data_file, errors, new_children
    #     else:
    #         return data_file, None, new_children
