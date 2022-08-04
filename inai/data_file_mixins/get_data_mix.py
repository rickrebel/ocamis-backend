
import json

raws = {}

def execute_matches(row, file):    
    from inai.models import NameColumn
    from formula.models import MissingRow, MissingField
    delegation = None
    missing_row = None
    if not state:
        columns_state = columns.filter(final_field__collection='State')
        if columns_state.exists():
            state = state_match(row, columns_state, 'State')
    #Delegación
    columns_deleg = columns.filter(final_field__collection='Delegation')
    if columns_deleg.exists():
        delegation = delegation_match(row, columns_state, 'Delegation')
        if not delegation:
            #missing_row = MissingRow.objects.get_or_create(file=file)
            missing_row = MissingRow.objects.create(
                file=file, row_seq = row[0], orinal_data=row)
        if delegation and not state:
            state = delegation.state
    recipe_row = []
    if not state:
        pass


class ExtractorsMix:

    def transform_file_in_data(self, is_explore, suffix):
        data_rows = []
        headers = []
        status_error = 'explore_fail' if is_explore else 'extraction_failed'
        if suffix in ['.txt', '.csv']:
            data_rows, errors = self.get_data_from_file_simple()
            print(data_rows[0])
            if errors:
                return self.save_errors(errors, status_error)
            file_control = self.petition_file_control.file_control
            validated_rows = self.divide_rows(data_rows, is_explore)
            row_headers = file_control.row_headers or 0
            if row_headers == 1:
                headers = validated_rows.pop(0)
            elif row_headers:
                errors = ["No podemos procesar ahora headers en posiciones distintas"]
                return self.save_errors(errors, status_error)
            pops_count = file_control.row_start_data - row_headers - 1
            print("pops_count", pops_count)
            for pop in range(pops_count):
                validated_rows.pop(0)
            print(validated_rows[0])
            print(validated_rows[4])
        elif suffix in ['.xlsx', '.xls']:
            headers, data_rows, errors = self.get_data_from_excel()
            validated_rows = data_rows
        if errors:
            return Response(
                {"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        #RICK: Pendiente este tema
        #meta_columns = 
        #if is_explore:
        #    data_rows = data_rows[:50]
        total_rows = len(data_rows)
        inserted_rows = 0
        completed_rows = 0
        #validated_rows = self.divide_rows(data_rows, is_explore)
        if is_explore:
            return {
                "headers": headers,
                "structured_data": validated_rows[:200]
            }
        print("despues de terminar")
        matched_rows = []
        for row in validated_rows:
            row = execute_matches(row, self)
            matched_rows.append(row)
        return matched_rows


    def divide_rows(self, data_rows, is_explore=False):
        global raws
        from inai.models import NameColumn
        from formula.models import MissingRow, MissingField
        file_control = self.petition_file_control.file_control
        current_columns = NameColumn.objects.filter(
            file_control=file_control)
        columns_count = current_columns.filter(
            position_in_data__isnull=False).count()
        delimiter = file_control.delimiter
        structured_data = []
        missing_data = []
        print("delimiter", delimiter)
        for row_seq, row in enumerate(data_rows, file_control.row_start_data):
            if row_seq < 5:
                print(row_seq, row)
            if delimiter:
                row_data = row.split(delimiter)
                if is_explore or len(row_data) == columns_count:
                    #row_data.insert(0, row_seq)
                    structured_data.append(row_data)
                else:
                    errors = ["Conteo distinto de Columnas: %s de %s" % (
                        len(row_data), columns_count)]
                    missing_data.append([self.id, row_data, row_seq, errors])
            if row_seq < 5:
                print(row_data)

        raws["missing_r"] = missing_data
        return structured_data

    def split_and_decompress(self):
        import os
        import zipfile 
        import pathlib
        from inai.models import StatusControl
        count_splited = 0
        #file_name = self.file_name
        suffixes = pathlib.Path(self.file.url).suffixes
        suffixes = set([suffix.lower() for suffix in suffixes])
        #format_file = self.file_control.format_file
        if '.gz' in suffixes:
            #print("path", self.file.path)
            print("name", self.file.url)
            print("url", self.file.url)
            success_decompress, final_path = self.decompress_file_gz()
            if not success_decompress:
                errors = ['No se pudo descomprimir el archivo gz %s' % final_path]            
                return None, errors, None
            file_without_extension = final_path
            print("final_path:", final_path)
            real_final_path = self.file.url.replace(".gz", "")
            #file_without_extension = file_path[:-3]
            decompressed_status, created = StatusControl.objects.get_or_create(
                name='decompressed', group="process")
            initial_status, created = StatusControl.objects.get_or_create(
                name='initial', group="process")
            self.status_process = decompressed_status
            self.save()
            prev_self_pk = self.pk
            new_file = self 
            #new_file.origin_file = self
            new_file.pk = None
            new_file.status_process = initial_status
            new_file.file.url = real_final_path
            new_file.save()
            new_file.origin_file_id = prev_self_pk
            new_file.save()
            self = new_file

            #self = new_file
            suffixes.remove('.gz')
        if 'zip' in suffixes:
            #[directory, only_name] = self.path.rsplit("/", 1)
            #[base_name, extension] = only_name.rsplit(".", 1)
            directory = self.file.url
            #path_imss_zip = "C:\\Users\\Ricardo\\recetas grandes\\Recetas IMSS\\Septiembre-20220712T233123Z-001.zip"
            zip_file = zipfile.ZipFile(self.file.url)
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
            return None, errors, None
        []
        #if not set(['.txt', '.csv', '.xls', '.xlsx']).issubset(suffixes):
        if not suffixes.issubset(set(['.txt', '.csv', '.xls', '.xlsx'])):
            errors = ["Formato no válido", u"%s" % suffixes]
            return None, errors, None
        #file_size = os.path.getsize(self.file_name)
        file_size = self.file.size
        if file_size > 400000000:
            if 'xlsx' in suffixes or 'xls' in suffixes:
                errors = ["Archivo excel muy grande, aún no se puede partir"]
                return None, errors, None
            count_splited = self.split_file()
        return count_splited, [], list(suffixes)[0]


    def decompress_file_gz(self):
        import gzip
        import shutil
        try:
            with gzip.open(self.file, 'rb') as f_in:
                decomp_path = self.file.url.replace(".gz", "")
                with open(decomp_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                    return True, decomp_path
        except Exception as e:
            return False, e


    #funcion de carga de Excel (solo listas sin nombres)
    #path_excel = 'D:\\Documents\\desabasto_ocamis\\pruebas_scripts\\prueba_clues.xlsx'
    #def import_excelnh(path_excel):
    def get_data_from_excel(self):
        import pandas as pd
        print("ESTOY EN EXCEEEEL")
        #prueba_clues = pd.read_excel(path_excel, dtype = 'string', nrows=50)
        data_excel = pd.read_excel(
            self.file.url, dtype = 'string', nrows=50)
        #Nombres de columnas (pandaarray)
        headers = data_excel.keys().array
        #Renglones de las variables
        #rows= []
        #for row in prueba_clues.iterrows():
        #    rows.append(row)
        #rows = [row for row in data_excel.iterrows()]
        #rowsf = [row[1] for row in data_excel.iterrows()]
        listval = [row[1].tolist() for row in data_excel.iterrows()]
        #rows = [row[0]+(row[1].tolist()) for row in data_excel.iterrows()]
        #print(rows)
        #Extraer datos de tuple (quitar nombre index)
        #rowsf = [a_row[1] for a_row in rows]
        #print("---------------------")
        #print("---------------------")
        #print(rowsf)
        #return [], []
        #print(rowsf)
        #print("---------------------")
        #print("---------------------")
        #Extraer datos a lista
        #listval=[]
        #for lis in rowsf:
        #    listval.append(lis.tolist())
        #Guardar con nombres
        #print(listval)
        return headers, listval, []




    def get_data_from_file_simple(self):
        from scripts.recipe_specials import (
            special_coma, special_excel, clean_special)
        import io
        try:
            with io.open(self.file.url, "r", encoding="latin-1") as file_open:
                data = file_open.read()
                file_open.close()
        except Exception as e:
            print(e)
            return False, [u"Error leyendo los datos %s" % e]
        """is_issste = self.petition_file_control.petition.entity.institution.code == 'ISSSTE'
        file_control = self.petition_file_control.file_control
        if "|" in data[:5000]:
            file_control.delimiter = '|'
        elif "," in data[:5000]:
            file_control.delimiter = ','
            if is_issste:
                data = special_coma(data)
                if ",,," in data[:5000]:
                    data = special_excel(data)
        #elif not set([',', '|']).issubset(data[:5000]):
        else:
            return False, ['El documento está vacío']
        file_control.save()
        if is_issste:
            data = clean_special(data)"""
        rr_data_rows = data.split("\n")
        return rr_data_rows, []
