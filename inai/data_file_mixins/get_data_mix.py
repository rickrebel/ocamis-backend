
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

    def transform_file_in_data(self, type_xplor, suffix, file_control=None):
        from category.models import FileFormat
        is_explore = bool(type_xplor)
        is_auto = type_xplor == 'auto_explore'
        status_error = 'explore_fail' if is_explore else 'extraction_failed'
        if not file_control:
            file_control = self.petition_file_control.file_control
        #if (".%s" % file_control.format_file) != suffix and (
        #    (".%sx" % file_control.format_file) != suffix):
        if not suffix in file_control.file_format.suffixes:
            errors = ["Formato especificado no coincide con el archivo"]
            #return self.save_errors(errors, status_error)
            return {"errors": errors}
        if suffix in ['.txt', '.csv']:
            data_rows, errors = self.get_data_from_file_simple(is_explore)
            if errors:
                return self.save_errors(errors, status_error)
            #print(data_rows[0])
            #print("LEN - data_rows: ", len(data_rows))
            if isinstance(data_rows, dict):
                validated_data = data_rows
            else:
                validated_data_default = self.divide_rows(
                    data_rows, file_control, is_explore)
                validated_data = {"default": 
                    {"all_data": validated_data_default[:200]}
                }
            current_sheets = ["default"]
        elif suffix in FileFormat.objects.get(short_name='xls').suffixes:
            validated_data, current_sheets, errors = self.get_data_from_excel(
                is_explore, file_control)
            if errors:
                return self.save_errors(errors, status_error)
        else:
            errors = ["No es un formato válido"]
            return self.save_errors(errors, status_error)
        #Ya no se hacen las extracciones porque se va a descubir el file_control
        #is_orphan = file_control.data_group.name == 'orphan'
        #if is_orphan:
        #    return validated_rows
        if is_explore:
            self.explore_data = validated_data
            self.save()
        row_headers = file_control.row_headers or 0
        #for sheet_name, all_data in validated_data.items():
        new_validated_data = {}
        for sheet_name in current_sheets:
            curr_sheet = validated_data.get(sheet_name).copy()            
            plus_rows = 0
            try:
                all_data = curr_sheet.get("all_data")
            except Exception as e:
                print("----------")
                print(curr_sheet)
                raise e
            if not "headers" in curr_sheet:
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
                        #if nulls:
                        #    continue
                    few_nulls = len(nulls) < 2
                if (few_nulls and headers) or not row_headers:
                    #plus_cols = 0 if headers[0] else 1
                    #validated_data[sheet_name]["plus_columns"] = plus_cols
                    start_data = file_control.row_start_data - 1 + plus_rows
                    curr_sheet["plus_rows"] = plus_rows
                    data_rows = all_data[start_data:][:200]
                    curr_sheet["data_rows"] = data_rows
                    #curr_sheet["headers"] = headers[plus_cols:]
                    curr_sheet["headers"] = headers
                else:
                    print("No pasó las pruebas básicas")
                    curr_sheet["headers"] = headers
                    curr_sheet["data_rows"] = all_data
                    pendiente_hasta_aca = 0
            new_validated_data[sheet_name] = curr_sheet
        #print(validated_rows[0])
        #print(validated_rows[4])
        #total_rows = len(validated_rows)
        
        #inserted_rows = 0
        #completed_rows = 0
        if is_explore:
            return {
                #"headers": headers,
                #"structured_data": validated_rows[:200]
                #"structured_data": validated_data,
                "structured_data": new_validated_data,
                "current_sheets": current_sheets,
            }
        return validated_rows  
        matched_rows = []
        for row in validated_rows:
            row = execute_matches(row, self)
            matched_rows.append(row)
        return matched_rows


    def divide_rows(self, data_rows, file_control, is_explore=False):
        global raws
        from inai.models import NameColumn
        from formula.models import MissingRow, MissingField
        current_columns = NameColumn.objects.filter(
            file_control=file_control)
        columns_count = current_columns.filter(
            position_in_data__isnull=False).count()
        structured_data = []
        missing_data = []
        #print("delimiter", delimiter)
        encoding = "utf-8"
        is_byte = isinstance(data_rows[3], bytes)
        is_latin = False
        for row_seq, row in enumerate(data_rows, 1):
            #if row_seq < 5:
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
            row_data = row.split(file_control.delimiter)
            if is_explore or len(row_data) == columns_count:
                #row_data.insert(0, row_seq)
                structured_data.append(row_data)
            else:
                errors = ["Conteo distinto de Columnas: %s de %s" % (
                    len(row_data), columns_count)]
                missing_data.append([self.id, row_data, row_seq, errors])
            #if row_seq < 5:
            #    print(row_data)

        raws["missing_r"] = missing_data
        return structured_data


    def get_data_from_excel(self, is_explore, file_control):
        import pandas as pd
        from inai.models import Transformation
        #print("ESTOY EN EXCEEEEL")
        #print(self.file.path)
        #print(self.file.url)
        #print(self.file.name)
        #print("---------")
        """data_excel = pd.read_excel(
            self.final_path, dtype='string', nrows=50,
            #converters=str.strip,
            na_filter=False,
            keep_default_na=False, header=None)"""
        excel_file = pd.ExcelFile(self.final_path)
        sheet_names = excel_file.sheet_names
        file_transformations = Transformation.objects.filter(
            file_control=file_control,
            clean_function__name__icontains="_tabs_")
        include_names = exclude_names = include_idx = exclude_idx = None
        nrows = 220 if is_explore else None
        if is_explore:
            all_sheets = self.explore_data or {}
        else:
            all_sheets = {}
        current_sheets = []

        for transf in file_transformations:
            current_vals = transf.addl_params["value"].split(",")
            func_name = transf.clean_function.name
            all_names = [name.upper().strip() for name in current_vals]
            if func_name == 'include_tabs_by_name':
                include_names = all_names
            elif func_name == 'exclude_tabs_by_name':
                exclude_names = all_names
            elif func_name == 'include_tabs_by_index':
                include_idx = [int(val.strip()) for val in current_vals]
            elif func_name == 'exclude_tabs_by_index':
                exclude_idx = [int(val.strip()) for val in current_vals]

        def clean_na(row):
            cols = row[1].tolist()
            return [col if isinstance(col, str) else "" for col in cols]

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
            #xls.parse(sheet_name)
            if is_explore and sheet_name in all_sheets:
                if "all_data" in all_sheets[sheet_name]:
                    continue
            data_excel = excel_file.parse(
                sheet_name,
                dtype='string', nrows=nrows, na_filter=False,
                keep_default_na=False, header=None)
            #listval = [row[1].tolist() for row in data_excel.iterrows()]
            listval = [clean_na(row) for row in data_excel.iterrows()]
            all_sheets[sheet_name] = {"all_data": listval[:200]}
            #all_sheets[sheet_name]["all_data"] = listval
            #return False, ["todo bien, checa prints"]
            #if file_control.file_transformations.clean_function
        #Nombres de columnas (pandaarray)
        #Renglones de las variables
        #rows= []
        #for row in prueba_clues.iterrows():
        #    rows.append(row)
        #rows = [row for row in data_excel.iterrows()]
        #rowsf = [row[1] for row in data_excel.iterrows()]
        
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
        return all_sheets, current_sheets, []


    def get_data_from_file_simple(self, is_explore):
        from scripts.recipe_specials import (
            special_coma, special_excel, clean_special)
        from django.conf import settings
        import io
        from scripts.common import get_file, start_session, create_file

        is_prod = getattr(settings, "IS_PRODUCTION", False)
        if is_explore and isinstance(self.explore_data, dict):
            if "all_data" in self.explore_data.get("default", {}):
                return self.explore_data, []

        if is_prod:
            s3_client, dev_resource = start_session()
            data = get_file(self, dev_resource)
            if isinstance(data, dict):
                if data.get("errors", False):
                    return False, data["errors"]
            #CORROBORAR SI ES NECEARIO ESTO ESTO:
            #data = data.read().decode('utf-8')
            #data = data.readlines(68000 if is_explore else 0).decode('utf-8')
            data = data.readlines()
            #if is_explore:
            #    data = data.readlines(68000)
            #else:
            #    data = data.readlines()
        else:
            try:
                with open(self.data.file, "r", encoding="UTF-8") as file_open:
                    #data = file_open.read()
                    data = file_open.readlines(68000 if is_explore else 0)
                    #data = file_open.readlines(68000 if is_explore else 0).decode('utf-8')
                    file_open.close()
            except Exception as e:
                print(e)
                return False, [u"Error leyendo los datos %s" % e]
        
        """
        is_issste = self.petition_file_control.petition.entity.institution.code == 'ISSSTE'
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
            data = clean_special(data)
        """
        return data, []

