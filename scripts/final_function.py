#Para nombres
def hydrateCol(row, all_headers):
    hydrated = {}
    cols = row
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


#Para cargar Excel
path_excel = 'D:\\Documents\\desabasto_ocamis\\pruebas_scripts\\prueba_clues.xlsx'
def import_excel(path_excel):
    import pandas as pd
    prueba_clues = pd.read_excel(path_excel, dtype = 'string', nrows=50)
    #Nombres de columnas (pandaarray)
    headers = prueba_clues.keys().array
    #Renglones de las variables
    rows= []
    for row in prueba_clues.iterrows():
        rows.append(row)
    #Extraer datos de tuple (quitar nombre index)
    rowsf= [a_row[1] for a_row in rows]
    print(rowsf)
    #Extraer datos a lista
    listval=[]
    for lis in rowsf:
        listval.append(lis.tolist())
    dtafin={}
    dtafin = hydrateCol(listval,headers)
    print(dtafin)
