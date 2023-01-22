import unidecode


def build_query_filter(row, columns):
    query_filter = {}
    for column in columns:
        name_column = column.final_field
        query_filter[name_column] = row[column.position_in_data]
    return query_filter

class ExploreMix:
    from category.models import FileFormat

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
            minus_headers = len(self.explore_data.keys()) * minus_headers
        self.change_status("success_counting")
        total_count = total_count - minus_headers
        self.total_rows = total_count
        self.save()
        return {"total_rows": total_count}

    def count_csv_rows(self):
        from scripts.common import get_file, start_session, get_csv_file
        import pandas as pd
        s3_client, dev_resource = start_session()
        data = get_file(self, dev_resource)
        final_count = len(data.readlines())
        return final_count

    def count_xls_rows(self):
        from scripts.common import get_file, start_session
        from django.conf import settings
        import pandas as pd
        #s3_client, dev_resource = start_session()
        #data = get_file(self, dev_resource)
        total_count = 0
        explore_data = self.explore_data
        explore_modificated = False
        #if not explore_data:

        if isinstance(explore_data, dict):
            current_sheets = explore_data.keys()
            #print("current_sheets: ", current_sheets)
            for sheet_name in current_sheets:
                if "total_rows" in explore_data[sheet_name]:
                    total_count += explore_data[sheet_name]["total_rows"]
                else:
                    #excel_file = pd.ExcelFile(self.file, sheet_name=sheet_name)
                    excel_file = pd.read_excel(self.file, sheet_name=sheet_name)
                    current_count = excel_file.shape[0]
                    explore_modificated = True
                    explore_data[sheet_name]["total_rows"] = current_count
                    total_count += current_count
        if explore_modificated:
            self.explore_data = explore_data
            self.save()
        return total_count

    #Comienzo del proceso de transformación.
    #Si es esploración (is_explore) solo va a obtener los headers y las 
    #primeras filas
    def start_file_process(self, is_explore=False):
        from rest_framework.response import Response
        from rest_framework import (permissions, views, status)
        from inai.models import DataFile
        #FieldFile.open(mode='rb')
        import json
        self.error_process = []
        self.save()
        #se llama a la función para descomprimir el archivo o archivos:
        new_self, errors, suffix = self.decompress_file()
        if errors:
            status_error = 'explore_fail' if is_explore else 'extraction_failed'
            return self.save_errors(errors, status_error)
        count_splited = 0
        file_size = new_self.file.size
        if file_size > 400000000:
            if suffix in FileFormat.objects.get(short_name='xls').suffixes:
                errors = ["Archivo excel muy grande, aún no se puede partir"]
                return None, errors, None
            count_splited = new_self.split_file()
        #return count_splited, [], list(suffixes)[0]

        if errors:
            status_error = 'explore_fail' if is_explore else 'extraction_failed'
            return new_self.save_errors(errors, status_error)
        if count_splited and not is_explore:
            warnings = [("Son muchos archivos y tardarán en"
                " procesarse, espera por favor")]
            return Response(
                {"errors": warnings}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        if not is_explore:
            new_self.build_catalogs()
        elif count_splited:
            #FALTA AFINAR FUNCIÓN PARA ESTO
            all_childs = DataFile.objects.filter(origin_file=new_self)
            for ch_file in all_childs:
                data = ch_file.transform_file_in_data('is_explore', suffix)
        else:
            data = new_self.transform_file_in_data('is_explore', suffix)
        if is_explore:
            #print(data["headers"])
            #print(data["structured_data"][:6])
            return data
        return data

    def find_coincidences(self, file_ctrl, suffix, saved):
        from inai.models import NameColumn, PetitionFileControl
        data = self.transform_file_in_data(
            'auto_explore', suffix, file_ctrl)
        if not data:
            return None
        if isinstance(data, dict):
            if data.get("errors", False):
                # print(data)
                return None
        # row_headers = file_ctrl.row_headers or 0
        # headers = data["headers"]
        current_sheets = data["current_sheets"]
        structured_data = data["structured_data"]
        all_pet_file_ctrl = []
        validated_data = self.explore_data or {}
        # print("-------\n-----------")
        # print(structured_data)
        # print("-------\n-----------")
        for sheet_name in current_sheets:
            if not "headers" in structured_data[sheet_name]:
                continue
            headers = structured_data[sheet_name]["headers"]
            headers = [head.strip() for head in headers]
            # headers = validated_rows[row_headers-1] if row_headers else []
            # validated_rows = validated_rows[file_ctrl.row_start_data-1:]
            name_columns = NameColumn.objects.filter(
                file_control=file_ctrl, name_in_data__isnull=False) \
                .values_list("name_in_data", flat=True)
            if headers and list(name_columns) == headers:
                succ_pet_file_ctrl, created_pfc = PetitionFileControl.objects \
                    .get_or_create(
                    file_control=file_ctrl, petition=petition)
                validated_data[sheet_name] = structured_data[sheet_name]
                if succ_pet_file_ctrl.id in all_pet_file_ctrl:
                    continue
                if saved:
                    info_text = "El archivo está en varios grupos de control"
                    self.add_result(("info", info_text))
                    new_data_file = self
                    new_data_file.pk = None
                    new_data_file.petition_file_control = succ_pet_file_ctrl
                    new_data_file.save()
                    new_data_file.add_result(("info", info_text))
                else:
                    self.petition_file_control = succ_pet_file_ctrl
                    self.save()
                    self.change_status("success_exploration")
                    saved = True
                all_pet_file_ctrl.append(succ_pet_file_ctrl.id)
        return saved

    def decompress_file(self):
        import os
        import zipfile 
        import pathlib
        from django.conf import settings
        from scripts.common import get_file, start_session, create_file
        from io import BytesIO
        from category.models import FileFormat
        import re
        #Se obienen todos los tipos del archivo inicial:
        print(self.final_path)
        suffixes = pathlib.Path(self.final_path).suffixes
        re_is_suffix = re.compile(r'^\.([a-z]{3,4})$')
        suffixes = [suffix.lower() for suffix in suffixes
            if bool(re.search(re_is_suffix, suffix)) or suffix == '.gz']
        print("suffixes", suffixes)
        all_errors = []
        if '.gz' in suffixes:
            #print("path", self.file.path)
            #print("name", self.file.name)
            #print("url", self.file.url)
            #Se llama a la función que descomprime el arhivo
            success_decompress, final_path = self.decompress_file_gz()
            print("final_path", final_path)
            if not success_decompress:
                print("error en success_decompress")
                errors = ['No se pudo descomprimir el archivo gz %s' % final_path]            
                return None, errors, None
            #print("final_path:", final_path)
            #Se vuelve a obtener la ubicación final del nuevo archivo
            # real_final_path = self.final_path.replace(".gz", "")
            #Como el archivo ya está descomprimido, se guarda sus status
            self.change_status('decompressed')

            # Se realiza todito el proceso para guardar el nuevo objeto DataFinal,
            # manteniendo todas las características del archivo original
            prev_self_pk = self.pk
            new_file = self 
            new_file.pk = None
            new_file.file = final_path
            #se guarda el nuevo objeto DataFinal
            new_file.save()
            #Se asigna su status y la referencia con el archivo original
            new_file.change_status("initial")
            new_file.origin_file_id = prev_self_pk
            new_file.save()
            #ahora es con el nuevo archivo con el que estamos tratando
            self = new_file
            suffixes.remove('.gz')
            print("new_suffixex",  suffixes)
        elif '.zip' in suffixes:
            #[directory, only_name] = self.path.rsplit("/", 1)
            #[base_name, extension] = only_name.rsplit(".", 1)
            """
            directory = self.final_path
            is_prod = getattr(settings, "IS_PRODUCTION", False)
            s3_client = None
            dev_resource = None
            if is_prod:
                s3_client, dev_resource = start_session()

            if is_prod:
                bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
                zip_obj = dev_resource.Object(
                    bucket_name=bucket_name, 
                    key=f"{settings.AWS_LOCATION}/{self.file.name}"
                    )
                buffer = BytesIO(zip_obj.get()["Body"].read())
            else:
                buffer = get_file(self, dev_resource)

            zip_file = zipfile.ZipFile(buffer)
            #all_files = zip_file.namelist()
            #infolist = zip_file.infolist()
            initial_status = StatusControl.objects.get(
                name='initial', group="process")
            #with zipfile.ZipFile(self.url, 'r') as zip_ref:
            #    zip_ref.extractall(directory)
            #ZipFile.extractall(path=None, members=None, pwd=None)   
            #for f in os.listdir(directory):
            for zip_elem in zip_file.infolist():
                if zip_elem.is_dir():
                    continue
                pos_slash = zip_elem.filename.rfind("/")
                only_name = zip_elem.filename[pos_slash + 1:]
                directory = (zip_elem.filename[:pos_slash]
                    if pos_slash > 0 else None)
                #z_file.open(filename).read()
                file_bytes = zip_file.open(zip_elem).read()

                curr_file, file_errors = create_file(
                    self, file_bytes, only_name, s3_client=s3_client)
                if file_errors:
                    all_errors += file_errors
                    continue
                new_file = self
                new_file.pk = None
                new_file = DataFile.objects.create(
                    file=curr_file,
                    origin_file=self,
                    date=self.date,
                    directory=directory,
                    status=initial_status,
                    #Revisar si lo más fácil es poner o no los siguientes:
                    file_control=file_control,
                    petition=self.petition,
                    petition_month=file.petition_month,
                    )
                self = new_file
            suffixes.remove('.zip')
            """
            error_zip = "Mover a 'archivos no finales' para descomprimir desde allí"
            return None, [error_zip], None

        #Obtener el tamaño
        #file_name = self.file_name
        real_suffixes = suffixes
        if len(real_suffixes) != 1:
            errors = [("Tiene más o menos extensiones de las que"
                " podemos reconocer: %s" % real_suffixes)]
            return None, errors, None
        real_suffixes = set(real_suffixes)
        readable_suffixes = FileFormat.objects.filter(readable=True)\
            .values_list("suffixes", flat=True)
        final_readeable = []
        for suff in list(readable_suffixes):
            final_readeable += suff
        #if not set(['.txt', '.csv', '.xls', '.xlsx']).issubset(suffixes):
        if not real_suffixes.issubset(final_readeable):
            errors = ["Formato no legible", u"%s" % suffixes]
            return None, errors, None
        return self, [], list(real_suffixes)[0]

    def decompress_file_gz(self):
        print("decompress_file_gz")
        import gzip
        import shutil
        from scripts.common import get_file, start_session, create_file
        from django.conf import settings
        is_prod = getattr(settings, "IS_PRODUCTION", False)

        try:
            if is_prod:
                s3_client, dev_resource = start_session()
                bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
                gz_obj = dev_resource.Object(
                    bucket_name=bucket_name, 
                    key=f"{settings.AWS_LOCATION}/{self.file.name}"
                    )
                with gzip.GzipFile(fileobj=gz_obj.get()["Body"]) as gzipfile:
                    content = gzipfile.read()
                    decomp_path = self.file.name.replace(".gz", "")
                    pos_slash = decomp_path.rfind("/")
                    only_name = decomp_path[pos_slash + 1:]
                    curr_file, file_errors = create_file(
                        self, content, only_name, s3_client=s3_client)
                    return True, curr_file
            else:
                with gzip.open(self.file, 'rb') as f_in:
                    #Se contruye el path del nuevo archivo:
                    decomp_path = self.final_path.replace(".gz", "")
                    with open(decomp_path, 'wb') as f_out:
                        #Se crea el nuevo archivo
                        shutil.copyfileobj(f_in, f_out)
                        return True, decomp_path
        except Exception as e:
            print("error", e)
            return False, e

    def split_file(self):
        from filesplit.split import Split
        from inai.models import DataFile
        from category.models import StatusControl
        import os
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

        initial_status = StatusControl.objects.get(
            name='initial', group="process")
        original_file = self.origin_file or self

        def write_splited_files(complete_file):
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

        """
        with open(data, "rt") as fl:
            #buf = fl.readlines(SIZE_HINT)
            #print("+++++++++++++++++++++")
            #print(len(buf))
            #fl.close()
            while True:
                buf = fl.readlines(SIZE_HINT)
                if not buf:
                    # we've read the entire file in, so we're done.
                    break
                rr_file_name = f"{directory}\\{base_name}_{file_num + 1}.{extension}"
                print("buf_size", len(buf))
                outFile = open(rr_file_name, "wt", encoding="UTF-8")
                outFile.writelines(buf)
                outFile.close()
                file_num += 1
                new_file = DataFile.objects.create(
                    file=rr_file_name,
                    origin_file=original_file,
                    date=original_file.date,
                    status_process=initial_status,
                    #Revisar si lo más fácil es poner o no los siguientes:
                    #file_control=original_file.file_control,
                    petition_file_control=original_file.petition_file_control,
                    #petition=original_file.petition,
                    petition_month=original_file.petition_month)
            fl.close()
        """
        print("SE LOGRARON:", file_num)
        #print("directory", directory)
        #print("only_name", only_name)
        #print("base_name", base_name)
        #print("extension", extension)
        return file_num
        if file_num > 0:
            #if self.origin_file:
            #    self.delete()
            #first_file_name = f"{directory}/{base_name}_1.{extension}"
            #first_file = DataFile.objects.get(file=first_file_name)
            new_file = DataFile.objects.filter(origin_file=self).first
            return new_file, file_num
        else:
            return self, 0



    #[directory, only_name] = self.path.rsplit("/", 1)
    #[base_name, extension] = only_name.rsplit(".", 1)
    def test_zip_file(self):
        import zipfile
        import datetime
        url = "C:\\Users\\Ricardo\\dev\\desabasto\\desabasto-api\\fixture\\zipfolder.zip"

        #directory = self.final_path
        directory = url
        #path_imss_zip = "C:\\Users\\Ricardo\\recetas grandes\\Recetas IMSS\\Septiembre-20220712T233123Z-001.zip"
        #zip_file = zipfile.ZipFile(self.final_path)
        zip_file = zipfile.ZipFile(url)
        all_files = zip_file.namelist()
        print(all_files)
        for curr_file in all_files:
            print(curr_file)

        initial_status = StatusControl.objects.get(
            name='initial', group="process")

        with zipfile.ZipFile(url, mode="r") as archive:
            for info in archive.infolist():
                print(f"Es directorio: {info.is_dir()}")
                print(f"Filename: {info.filename}")
                print(f"Internal attr: {info.internal_attr}")
                print(f"External attr: {info.external_attr}")
                print(f"Modified: {datetime.datetime(*info.date_time)}")
                print(f"Normal size: {info.file_size} bytes")
                print(f"Compressed size: {info.compress_size} bytes")
                print("-" * 20)
            archive.close()

        #with zipfile.ZipFile(self.url, 'r') as zip_ref:
        with zipfile.ZipFile(url, 'r') as zip_ref:
            zip_ref.extractall(directory)               
        #ZipFile.extractall(path=None, members=None, pwd=None)   
        #for f in os.listdir(directory):
        for f in all_files:
            new_file = self
            new_file.pk = None
            new_file = DataFile.objects.create(
                file="%s%s" % (directory, f),
                origin_file=self,
                date=self.date,
                status=initial_status,
                #Revisar si lo más fácil es poner o no los siguientes:
                file_control=file_control,
                petition=self.petition,
                petition_month=file.petition_month,
                )
        self = new_file
        suffixes.remove('.zip')
