import unidecode


def build_query_filter(row, columns):
    query_filter = {}
    for column in columns:
        name_column = column.final_field
        query_filter[name_column] = row[column.position_in_data]
    return query_filter



class ExploreMix:

    def get_table_ref(self):
        print(self)
        return 2

    #Comienzo del proceso de transformación.
    #Si es esploración (is_explore) solo va a obtener los headers y las 
    #primeras filas
    def start_file_process(self, is_explore=False):
        from rest_framework.response import Response
        from rest_framework import (permissions, views, status)        
        from category.models import StatusControl
        from data_param.models import FinalField
        #FieldFile.open(mode='rb')
        import json
        self.error_process = []
        self.save()
        #se llama a la función para descomprimir el archivo o archivos:
        errors, suffix = self.decompress()
        count_splited = 0
        file_size = self.file.size
        if file_size > 400000000:
            if 'xlsx' in suffixes or 'xls' in suffixes:
                errors = ["Archivo excel muy grande, aún no se puede partir"]
                return None, errors, None
            count_splited = self.split_file()
        #return count_splited, [], list(suffixes)[0]

        if errors:
            status_error = 'explore_fail' if is_explore else 'extraction_failed'
            return self.save_errors(errors, status_error)
        if count_splited and not is_explore:
            warnings = [("Son muchos archivos y tardarán en"
                " procesarse, espera por favor")]
            return Response(
                {"errors": warnings}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        if not is_explore:
            self.build_catalogs()
        elif count_splited:
            #FALTA AFINAR FUNCIÓN PARA ESTO
            for ch_file in self.child_files:
                data = ch_file.transform_file_in_data(is_explore, suffix)
        else:
            #print("HOLA TERMINO")
            data = self.transform_file_in_data(is_explore, suffix)
            #print("HOLA TERMINO2")
        if is_explore:
            #print(data["headers"])
            #print(data["structured_data"][:6])
            return data
        return data

    #se descomprimen los comprimidos
    def decompress(self):
        import os
        import zipfile 
        import pathlib
        from inai.models import StatusControl
        #Se obienen todos los tipos del archivo inicial:
        print(self.final_path)
        suffixes = pathlib.Path(self.final_path).suffixes
        suffixes = set([suffix.lower() for suffix in suffixes])
        #format_file = self.file_control.format_file
        if '.gz' in suffixes:
            #print("path", self.file.path)
            #print("name", self.file.name)
            #print("url", self.file.url)
            #Se llama a la función que descomprime el arhivo
            success_decompress, final_path = self.decompress_file_gz()
            if not success_decompress:
                errors = ['No se pudo descomprimir el archivo gz %s' % final_path]            
                return errors, None
            #print("final_path:", final_path)
            #Se vuelve a obtener la ubicación final del nuevo archivo
            real_final_path = self.final_path.replace(".gz", "")
            #Como el archivo ya está descomprimido, se guarda sus status
            self.change_status('decompressed')

            #Se realiza todo el proceso para guardar el nuevo objeto DataFinal,
            # manteniendo todas las características del archivo original
            prev_self_pk = self.pk
            new_file = self 
            new_file.pk = None
            new_file.final_path = real_final_path
            #se guarda el nuevo objeto DataFinal
            new_file.save()
            #Se asigna su status y la referencia con el archivo original
            new_file.change_status("initial")
            new_file.origin_file_id = prev_self_pk
            new_file.save()
            #ahora es con el nuevo archivo con el que estamos tratando
            self = new_file
            suffixes.remove('.gz')
        if 'zip' in suffixes:
            #[directory, only_name] = self.path.rsplit("/", 1)
            #[base_name, extension] = only_name.rsplit(".", 1)
            directory = self.final_path
            #path_imss_zip = "C:\\Users\\Ricardo\\recetas grandes\\Recetas IMSS\\Septiembre-20220712T233123Z-001.zip"
            zip_file = zipfile.ZipFile(self.final_path)
            all_files = zip_file.namelist()
            with zipfile.ZipFile(self.url, 'r') as zip_ref:
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
        #Obtener el tamaño
        #file_name = self.file_name
        if (len(suffixes) != 1):
            errors = [("Tiene más o menos extensiones de las que"
                " podemos reconocer: %s" % suffixes)]
            return errors, None
        []
        #if not set(['.txt', '.csv', '.xls', '.xlsx']).issubset(suffixes):
        if not suffixes.issubset(set(['.txt', '.csv', '.xls', '.xlsx'])):
            errors = ["Formato no válido", u"%s" % suffixes]
            return errors, None
        return [], list(suffixes)[0]

    def decompress_file_gz(self):
        import gzip
        import shutil
        try:
            with gzip.open(self.file, 'rb') as f_in:
                #Se contruye el path del nuevo archivo:
                decomp_path = self.final_path.replace(".gz", "")
                with open(decomp_path, 'wb') as f_out:
                    #Se crea el nuevo archivo
                    shutil.copyfileobj(f_in, f_out)
                    return True, decomp_path
        except Exception as e:
            return False, e

    #def split_file(path="G:/My Drive/YEEKO/Clientes/OCAMIS/imss"):
    def split_file(self):
        from filesplit.split import Split
        from inai.models import File
        from category.models import StatusControl
        [directory, only_name] = self.file_name.rsplit("/", 1)
        [base_name, extension] = only_name.rsplit(".", 1)
        curr_split = Split(self.file_name, directory)
        curr_split.bylinecount(linecount=1000000)
        initial_status = StatusControl.objects.get_or_create(
            name='initial')
        count_splited = 0
        original_file = self.origin_file or self
        for file_num in range(99):
            rr_file_name = "%s_%s.%s" % (base_name, file_num + 1, extension)
            if not os.path.exists(rr_file_name):
                print("Invalid path", rr_file_name)
                break
            if not os.path.isfile(reporte_recetas_path):
                print("Invalid path")
                break
            new_file = File.objects.create(
                self=rr_file_name,
                origin_file=original_file,
                date=original_file.date,
                status=initial_status,
                #Revisar si lo más fácil es poner o no los siguientes:
                #file_control=original_file.file_control,
                file_control=original_file.petition_file_control.file_control,
                petition=original_file.petition,
                petition_month=original_file.petition_month)
            count_splited += 1
        if count_splited > 0:
            if self.origin_file:
                self.delete()
            first_file_name = "%s_%s.%s" % (base_name, 1, extension)
            first_file = File.objects.get(file=first_file_name)
            return first_file, count_splited
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
