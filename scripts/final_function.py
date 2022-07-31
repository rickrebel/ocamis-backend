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
    #print(rowsf)
    #Extraer datos a lista
    listval=[]
    for lis in rowsf:
        listval.append(lis.tolist())
    #Guardar con nombres
    listfin=[]
    for lis in range(len(listval)):
        dict = hydrateCol(listval[lis],headers)
        listfin.append(dict)
    return(listfin)


#Corregir
#Identificar los movimientos de clues despues del 2019-12-31
from datetime import date
dates_idm =[]
datet = date.fromisoformat('2019-12-31')
for i in flist[32]:
    #datesm.append(date.fromisoformat(i)) 
    if (date.fromisoformat(i)) > datet: 
        dates_idm.append("True")
    else:
        dates_idm.append("False")
