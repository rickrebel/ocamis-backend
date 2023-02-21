def build_query_filter(row, columns):
    query_filter = {}
    for column in columns:
        name_column = column.final_field
        query_filter[name_column] = row[column.position_in_data]
    return query_filter


class ExploreMix:
    final_path: str
    petition_file_control: None

    def get_table_ref(self):
        print(self)
        return 2

    def count_file_rows(self):
        file_control = self.petition_file_control.file_control
        file_format = file_control.file_format
        total_count = 0
        minus_headers = file_control.row_start_data - 1
        if file_format.short_name == 'csv' or file_format.short_name == 'txt':
            total_count = self.count_csv_rows()
        elif file_format.short_name == 'xls':
            total_count = self.count_xls_rows()
            minus_headers = len(self.sample_data.keys()) * minus_headers
        total_count = total_count - minus_headers
        self.total_rows = total_count
        #self.save()
        self.change_status("success_counting")
        return {"total_rows": total_count}

    def count_csv_rows(self):
        from scripts.common import get_file, start_session
        s3_client, dev_resource = start_session()
        data = get_file(self, dev_resource)
        final_count = len(data.readlines())
        return final_count

    def count_xls_rows(self):
        from scripts.common import build_s3
        from task.serverless import count_excel_rows
        total_count = 0
        sample_data = self.sample_data
        explore_modificated = False

        if isinstance(sample_data, dict):
            current_sheets = sample_data.keys()
            #print("current_sheets: ", current_sheets)
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
            data_file.save_errors(errors, "explore_fail")
            return [], errors, None
        return [], errors, None

    def find_coincidences(
            self, saved=False, petition=None, file_ctrl=None,
            parent=None, task_params=None, **kwargs):
        from inai.models import NameColumn, PetitionFileControl
        data_file = self
        if not parent:
            parent = data_file
        data, errors, new_task = data_file.transform_file_in_data(
            'auto_explore', task_params=task_params, file_control=file_ctrl)
        if not petition or not file_ctrl:
            pfc = data_file.petition_file_control
            if not petition:
                petition = pfc.petition
            if not file_ctrl:
                file_ctrl = pfc.file_control
        # if not data:
        if errors:
            # errors.append("No se pudo explorar el archivo")
            return data_file, saved, errors
        if not data and not errors and not new_task:
            return data_file, saved, errors
        # row_headers = file_ctrl.row_headers or 0
        # headers = data["headers"]
        current_sheets = data["current_sheets"]
        structured_data = data["structured_data"]
        all_pet_file_ctrl = []
        validated_data = data_file.sample_data or {}
        for sheet_name in current_sheets:
            if "headers" not in structured_data[sheet_name]:
                continue
            headers = structured_data[sheet_name]["headers"]
            headers = [head.strip() for head in headers]
            # headers = validated_rows[row_headers-1] if row_headers else []
            # validated_rows = validated_rows[file_ctrl.row_start_data-1:]
            name_columns = NameColumn.objects.filter(
                file_control=file_ctrl, name_in_data__isnull=False) \
                .values_list("name_in_data", flat=True)
            if headers and list(name_columns) == headers:
                try:
                    succ_pet_file_ctrl, created_pfc = PetitionFileControl.objects \
                        .get_or_create(
                            file_control=file_ctrl, petition=petition)
                except PetitionFileControl.MultipleObjectsReturned:
                    errors = ["El grupos de control está duplicado en la solicitud"]
                    return data_file, saved, errors
                validated_data[sheet_name] = structured_data[sheet_name]
                if succ_pet_file_ctrl.id in all_pet_file_ctrl:
                    continue
                if saved:
                    info_text = "El archivo está en varios grupos de control"
                    data_file.add_result(("info", info_text))
                    new_data_file = data_file
                    new_data_file.pk = None
                    new_data_file.petition_file_control = succ_pet_file_ctrl
                    new_data_file.sample_data = validated_data
                    new_data_file.save()
                    new_data_file.add_result(("info", info_text))
                else:
                    data_file.petition_file_control = succ_pet_file_ctrl
                    data_file.sample_data = validated_data
                    data_file.change_status("success_exploration")
                    saved = True
                all_pet_file_ctrl.append(succ_pet_file_ctrl.id)
        return data_file, saved, []

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
            self = self.change_status('decompressed')
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
            errors = ["Formato no legible", u"%s" % suffixes]
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
                    self, buf, curr_only_name, current_s3_client)
                print("exito en creación de archivo")
                print("errors", errors)
                DataFile.objects.create(
                    file=rr_file_name,
                    origin_file=self,
                    date=self.date,
                    status_process=initial_status,
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
                        self, buf, curr_only_name, s3_client)
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
            x, y, data_file = self.explore_data_xls_after(**kwargs)
            parent_task = task_params.get("parent_task", None)
            if parent_task.params_after:
                kwargs.update(parent_task.params_after)
        else:
            data_file = self
        return data_file, kwargs

    def find_matches_in_file_controls(self, task_params=None, **kwargs):
        from inai.models import FileControl
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
            data_file.save_errors(all_errors, "explore_fail")
        return None, all_errors, None

    def build_complex_headers(self, task_params=None, **kwargs):
        from inai.models import NameColumn

        data_file = self
        all_errors = []
        data, errors, new_task = data_file.transform_file_in_data(
            'auto_explore', task_params=task_params)
        if errors:
            all_errors.extend(errors)
            data_file.save_errors(all_errors, "explore_fail")
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
        print("current_sheets", current_sheets)
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
            status_error = 'explore_fail' if is_explore else 'extraction_failed'
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
            status_error = 'explore_fail' if is_explore else 'extraction_failed'
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

    def comprobate_coincidences(self, task_params=None, **kwargs):
        from inai.models import DataFile
        # print("new_children_ids: ", new_children_ids)
        data_file, kwargs = self.corroborate_save_data(task_params, **kwargs)
        from_aws = kwargs.get("from_aws", False)

        file_ctrl = data_file.petition_file_control.file_control
        petition = data_file.petition_file_control.petition

        parent_task = task_params.get("parent_task", None)
        if from_aws:
            new_children_ids = kwargs.get("new_children_ids", [])
            new_children = DataFile.objects.filter(id__in=new_children_ids)
        else:
            init_children = list(
                self.child_files.all().values_list('id', flat=True))
            # RICK 14
            (data_file, errors, suffix), first_task = self.decompress_file()
            if not data_file:
                print("______data_file:\n", data_file, "\n", "errors:", errors, "\n")
                return None, errors, 0
            new_children = data_file.child_files.all()
            if init_children:
                new_children = new_children.exclude(id__in=init_children)
            new_children_ids = new_children.values_list('id', flat=True)

        task_params = task_params or {}
        params_after = task_params.get("params_after", { })
        params_after["new_children_ids"] = list(new_children_ids)
        # params_after["all_file_controls_ids"] = [file_ctrl.id]
        task_params["params_after"] = params_after
        task_params["function_after"] = "comprobate_coincidences"
        task_params["models"] = [data_file]

        if not new_children_ids:
            data_file, errors, new_task = data_file.transform_file_in_data(
                'only_save', file_control=file_ctrl,
                task_params=task_params)
            if new_task:
                return data_file, errors, 0
            if not data_file:
                print("NO ENTIENDO QUÉ PASÓ")
                return None, errors, 0
            data_file, saved, errors = data_file.find_coincidences(
                False, petition=petition, file_ctrl=file_ctrl)
        else:
            print("HAY NUEVOS CHILDREN")
            first_child = new_children.first()
            first_child, errors, new_task = first_child.transform_file_in_data(
                'only_save', file_control=file_ctrl,
                task_params=task_params)
            if new_task:
                return first_child, errors, 0, new_task
            first_child, saved, errors = first_child.find_coincidences(
                False, petition=petition, file_ctrl=file_ctrl)
            if saved:
                for child in new_children:
                    child.sample_data = first_child.sample_data
                    child.status_process = first_child.status_process
                    child.save()
                data_file.sample_data = first_child.sample_data
                data_file.status_process = first_child.status_process
                data_file = data_file.save()

        if not errors and not saved and file_ctrl.row_headers:
            errors.append("Las columnas no coincide con el archivo")
            # errors = ["No hay coincidencias con las columnas"]
        if errors:
            data_file = data_file.save_errors(errors, "explore_fail")
            return data_file, errors, new_children
        else:
            return data_file, None, new_children
