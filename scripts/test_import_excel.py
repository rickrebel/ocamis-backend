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


def test_data_from_file():
    path_imss = "G:\\My Drive\\YEEKO\\Clientes\\OCAMIS\\imss\\req_septiembre_2020_02_1.txt"
    number_columns = 14
    row_start_data = 1
    row_headers = None
    final_data, headers, error_number_columns = get_data_from_file_txt(
        path_imss, number_columns, row_start_data, row_headers)
    print("rows_count: ", len(final_data)) ## 1,000,000
    print("headers: ", headers) ## None
    print("error_number_columns: ", error_number_columns) ## 0
    print("primeros datos:\n", final_data[:20]) ## [[----],[----],...]


##Pruebas

#Abrir excel
#PS: python -m pip install pandas
import pandas as pd
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

#Prueba
def get_data_from_excel(
        reporte_recetas_path, number_columns,
        row_start_data=None, row_headers=None):
#Nombre archivo:

new_name = f'{Path(fname).stem}.xlsx'

    with open(new_name, 'w') as xlsx_file:
        writer = xlsx.writer(csv_file, delimiter=',')
        writer.writerows(text_reader)





#Segunda parte de la funcion
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


def get_data_from_excel(
        reporte_recetas_path, number_columns,
        row_start_data=None, row_headers=None):
    return [[]], None, 0


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
