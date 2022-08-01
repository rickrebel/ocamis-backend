#Ejemplo para probar funcion que prueba txt
def test_data_from_file():
    #path_imss = "C:\\Users\\iakar\\Desktop\\desabasto\\pruebas_scripts\\req_septiembre_2020_02_1.txt"
    path_imss = "C:\\Users\\Ricardo\\Desktop\\experimentos\\SOLICITUDES_33_2022_19296.json"
    number_columns = 14
    row_start_data = 1
    row_headers = None
    final_data, headers, error_number_columns = get_data_from_file_txt(
        path_imss, number_columns, row_start_data, row_headers)
    print("rows_count: ", len(final_data)) ## 1,000,000
    print("headers: ", headers) ## None
    print("error_number_columns: ", error_number_columns) ## 0
    print("primeros datos:\n", final_data[:20]) ## [[----],[----],...]


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
    data_rows = data.replace("\r\n","\n")
    #data_rows = data.split("\n")
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

def intento_de_limpieza():
    import io
    import csv
    import json
    data = None
    path_json = "C:\\Users\\Ricardo\\Desktop\\experimentos\\sol19296_0.json"
    with io.open(path_json, "r", encoding="latin-1") as file:
        data = file.read()
        file.close()
    #data_json = data.replace('\r', '').replace('\n', '')
    #Enmedio de DescripcionSolicitud y FechaRespuesta
    data_file = data.replace("\n","\\n")
    #Lo que está fuera
    data_file = data_file.replace('\n', '')
    csv_path2 = "C:\\Users\\Ricardo\\Desktop\\experimentos\\sol19296_1.json"
    with open(csv_path2, 'w', encoding="latin-1") as outfile:
        outfile.write(data_file)


    data_file = data.replace("}\n,","},")
    print(data_file.count("}\n,"))
    print(data_file.count("\n"))

    print(data_file.count("\\n"))
    data_file = data.replace("}\\n,{", "},\n{")
    print(data_file.count("\\n"))
    print(data_file.count("\n"))
    #print(data_file[:6000])
    #primeros = data_file[:6000]
    #segundos = primeros.replace("\\n,{","|")
    #print("\n," in segundos)
    #data_file = data.replace("}\n,","},")
    #segundos = primeros.replace("}\n,","},")


    """with open(csv_path, 'w', encoding="latin-1", newline="") as csv_file:
        csv_path = "C:\\Users\\Ricardo\\Desktop\\experimentos\\SOLICITUDES_33_2022_19296CLEAN.json"
        write = csv.writer(csv_file, delimiter='|')
        write.writerows(data_file)
        csv_file.close()"""

        



