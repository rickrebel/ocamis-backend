
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
            if errors:
                return self.save_errors(errors, status_error)
            #print(data_rows[0])
            validated_rows = self.divide_rows(data_rows, is_explore)
        elif suffix in ['.xlsx', '.xls']:
            validated_rows, errors = self.get_data_from_excel()
            if errors:
                return self.save_errors(errors, status_error)
        if errors:
            return Response(
                {"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        file_control = self.petition_file_control.file_control
        row_headers = file_control.row_headers or 0
        headers = validated_rows[row_headers-1] if row_headers else []
        validated_rows = validated_rows[file_control.row_start_data-1:]
        #print(validated_rows[0])
        #print(validated_rows[4])
        total_rows = len(validated_rows)
        inserted_rows = 0
        completed_rows = 0
        #validated_rows = self.divide_rows(data_rows, is_explore)
        if is_explore:
            return {
                "headers": headers,
                "structured_data": validated_rows[:200]
            }
        print("despues de terminar")
        return validated_rows  
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


    def get_data_from_excel(self):
        import pandas as pd
        #print("ESTOY EN EXCEEEEL")
        #print(self.file.path)
        #print(self.file.url)
        #print(self.file.name)
        #print("---------")
        data_excel = pd.read_excel(
            self.final_path, dtype = 'string', nrows=50,
            #converters=str.strip,
            keep_default_na=False, header=None)
        #Nombres de columnas (pandaarray)
        #Renglones de las variables
        #rows= []
        #for row in prueba_clues.iterrows():
        #    rows.append(row)
        #rows = [row for row in data_excel.iterrows()]
        #rowsf = [row[1] for row in data_excel.iterrows()]
        listval = [row[1].tolist() for row in data_excel.iterrows()]
        #rows = [row[0]+(row[1].tolist()) for row in data_excel.iterrows()]
        #Extraer datos de tuple (quitar nombre index)
        #rowsf = [a_row[1] for a_row in rows]
        #Extraer datos a lista
        #listval=[]
        #for lis in rowsf:
        #    listval.append(lis.tolist())
        #Guardar con nombres
        #print(listval)
        #return headers, listval, []
        return listval, []


    def get_data_from_file_simple(self):
        from scripts.recipe_specials import (
            special_coma, special_excel, clean_special)
        from django.conf import settings
        import boto3
        import io
        is_prod = getattr(settings, "IS_PRODUCTION", False)
        if is_prod:
            print("PATH -- URL -- NAME")
            print(self.file.path)
            print(self.file.url)
            print(self.file.name)
            print("---------")

            try:
                bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
                aws_access_key_id = getattr(settings, "AWS_ACCESS_KEY_ID")
                aws_secret_access_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
                s3 = boto3.resource(
                    's3', aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key)
                content_object = s3.Object(bucket_name, self.file.path)
                data = content_object.get()['Body'].read().decode('utf-8')
            except Exception as e:
                print(e)
                return False, [u"Error leyendo los datos %s" % e]
        else:
            try:
                with io.open(self.final_path, "r", encoding="UTF-8") as file_open:
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

