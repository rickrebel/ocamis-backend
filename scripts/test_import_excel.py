
#Ejemplo de funcion para cargar txt
def get_data_from_file_txt(
        reporte_recetas_path, number_columns,
        row_start_data=None, row_headers=None):
    import io
    from django.utils import timezone
    try:
        with io.open(reporte_recetas_path, "r", encoding="latin-1") as file:
            data = file.read()
            file.close()
    except Exception as e:
        print(e)
        return False, [u"%s" % (e)], False
    data_rows = data.split("\n")
    final_data = []
    headers = None
    error_number_columns = 0
    for index, data_row in enumerate(data_rows):
        if index % 100000 == 0:
            print("index: %s" % index, timezone.now())
        final_row = data_row.split("|")
        if row_headers and index + 1 == row_headers:
            headers = final_row
        elif len(final_row) == number_columns:
            final_data.append(final_row)
        elif data_row:
            error_number_columns += 1
    return final_data, headers, error_number_columns

#Ejemplo para probar funcion que prueba txt
def test_data_from_file():
    path_imss = "C:\\Users\\iakar\\Desktop\\desabasto\\pruebas_scripts\\req_septiembre_2020_02_1.txt"
    number_columns = 14
    row_start_data = 1
    row_headers = None
    final_data, headers, error_number_columns = get_data_from_file_txt(
        path_imss, number_columns, row_start_data, row_headers)
    print("rows_count: ", len(final_data)) ## 1,000,000
    print("headers: ", headers) ## None
    print("error_number_columns: ", error_number_columns) ## 0
    print("primeros datos:\n", final_data[:20]) ## [[----],[----],...]


##FUNCION PARA CARAGA XLSX

one_path= #direccion donde se encuentra el archivo de excel 

#Para cargar xslx
def get_data_from_excel(file, is_explore,empty_row: int= 0):
    import pandas as pd
    import io
    from django.utils import timezone
    from files_rows.models import Column 
    one_path = file.file_name
    try:
        if not is_explore:
            columns = Column.objects.filter(group_file=file.group_file)
            dtype= {}
            for column in columns:
                name_pandas = column.type_data.addl_params["name_pandas"] 
                colum_name = column.name_in_data
                dtype[colum_name] = name_pandas
        if is_explore:
            dtype = "string"
        data = pd.read_excel(io=one_path, usecols='B:T', 
                dtype=dtype,
                sheet_name='Hoja_1', skiprows= empty_row,         
                dtype = dtype)
    except Exception as e:
        print(e)
        return False, [u"%s" % (e)], False

###DUDAS DE FUNCION:
## Quien use la función asignara el parametro como path o como nombre del documento
## Se asigna use el parametro 'usecols' dentro del comando read_excel sacando la columna A folio rep, se puede hacer un parametro para que se asigne que columnas se deben scar

        '''data= pd.read_excel(io=one_path)
        with open(data) as frows:  #Era para contar el numero de filas vacías
            empty_row= sum(line.isspace() for line in f) #Esto era para contar las filas vacias '''

##funcion para porbar carga
def test_data_from_file():
    path_imss = "C:\\Users\\iakar\\Desktop\\desabasto\\pruebas_scripts\\req_septiembre_2020_02_1.txt"
    number_columns = 14
    row_start_data = 1
    row_headers = None
    final_data, headers, error_number_columns = get_data_from_file_txt(
        path_imss, number_columns, row_start_data, row_headers)
    print("rows_count: ", len(final_data)) ## 1,000,000
    print("headers: ", headers) ## None
    print("error_number_columns: ", error_number_columns) ## 0
    print("primeros datos:\n", final_data[:20]) ## [[----],[----],...]


#Prueba
#Carga de varios archivos de Excel de manera automatizada
#Esta parte se puede hacer una funcion para caragar todo de manera automatizada
one_path= #direcciones donde se encuntran los archivos
mes= #lista de meses
from catalog.models import Delegation
from files_rows.models import GroupFile
from parameter.models import TypeData #obtencion del nombre de la delagacion, el cual esta contenido en el nombre del archivo
    deleg_nom = Delegation.objects.filter(name=name).first()













##Pruebas no usadas
'''
#Abrir excel
#PS: python -m pip install pandas
import pandas as pd

from catalog.models import Delegation
reporte_recetas= "C:\\Users\\iakar\\Desktop\\desabasto\\pruebas_scripts\\Agosto 2021-Pediatria SXXI.xlsx"
reporte= pd.read_excel(reporte_recetas)

#Primera parte de la funcion 
def get_data_from_excel(
        reporte_recetas_path, number_columns,
        row_start_data=None, row_headers=None):
    import io
    import pandas as pd
    from django.utils import timezone
    try:
        with io.open(reporte_recetas_path, "r", encoding="latin-1") as file:
            data = file.read()
            file.close()
    except Exception as e:
        print(e)
        return False, [u"%s" % (e)], False

###Prueba de la primera parte de la funcion 
get_data_from_excel(reporte,20)

#Error: expected str, bytes or os.PathLike object, not DataFrame
#Transform dataframe to str or modify the funtion without the commands str
#Transformar df to str
reporte = reporte.applymap(str)
pd.read_excel(reporte_recetas, dtype=str)
#Error: expected str, bytes or os.PathLike object, not DataFrame

#Alternativa
#You're passing open an already opened file, rather than the path of the file you created.

def split_file(path="G:/My Drive/YEEKO/Clientes/OCAMIS/imss"):
    from filesplit.split import Split
    curr_split = Split("%s/req_septiembre_2020_02.txt" % path, path)
    curr_split.bylinecount(linecount=1000000)

path="D:\Documents\desabasto_ocamis\pruebas_scripts"
months=["Agosto"]
years=["2021"]
def unpload_xlsx_files(path="",months="",years=""):
    import os
    from year in year:
        for mon in months:
            basee= "%s %s %s"(path, months, years) 


def test_data_from_excel():
    path_imss_xlsx = "C:\\Users\\Ricardo\\issste\\recetas_enero_durango.xlsx"
    number_columns = 20
    row_start_data = 2
    row_headers = 1
    final_data, headers, error_number_columns = get_data_from_excel(
        path_recetas, number_columns, row_start_data, row_headers)
    print("rows_count: ", len(final_data)) ## 3,616
    print("headers: ", headers) ## ["FOLIO REPORTE","NOMBRE DELEGACION", "NOMBRE UNIDAD", ...]
    print("error_number_columns: ", error_number_columns) ## 0
    print("primeros datos:\n", final_data[:20]) ## [[----],[----],...]
    print("Tiene bien los acentos?")


###############################################################
##PARA PROBAR OTRAS COSAS
#despues de haber cargado los xlsx se debe ver su estructura para 


def get_state(state_name):
    from desabasto.models import State

    try:
        state_name = unidecode.unidecode(state_name).upper()
    except Exception:
        state_name = state_name.upper()
    global catalog_state
    if not catalog_state:
        for state in State.objects.all():
            try:
                state.name = unidecode.unidecode(state.name).upper()
            except Exception:
                state.name = state.name.upper()
            catalog_state[state.name] = state

    if state_name not in catalog_state:
        state_obj = State.objects.create(inegi_code="xx", name=state_name)
        catalog_state[state_name] = state_obj

    return catalog_state[state_name]


file_path_ej="D:\\Documents\\desabasto_ocamis\\pruebas_scripts\\subcats.csv"

##Caraga de archivo csv
def getFileCsv(file_path):
    import io
    with io.open(file_path, "r", encoding="utf-8") as file:
        data = file.read() #leer el archivo
        rr_data_rows = data.split("\n") #dividir las columnas
        headers = rr_data_rows.pop(0) #hacer encabezado
        all_headers = headers.split("|") #dividir encabezados
        print(all_headers) 
        return all_headers, rr_data_rows

def hydrateCol(row, all_headers):
    hydrated = {}
    cols = row.split("|")
    if not len(cols):
        return False
    for idx_head, header in enumerate(all_headers):
        try:
            hydrated[header] = cols[idx_head]
        except Exception as e:
            print(cols)
            print(hydrated)
            return False
    return hydrated

'''

