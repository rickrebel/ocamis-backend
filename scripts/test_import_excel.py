
##FUNCIONES FINALES 30/07/22

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










##28/07/2022
###ELEMENTOS PARA LA FUNCION DE CARGA CLUES 

#################################

#Para cargar las clues
import pandas as pd
#def import_excel(path_excel):
path_excel = 'D:\\Documents\\desabasto_ocamis\\pruebas_scripts\\prueba_clues.xlsx'
prueba_clues = pd.read_excel(path_excel, dtype = 'string', nrows=50)

#Nombres de columnas (pandaarray)
headers = prueba_clues.keys().array

#Renglones de las variables
rows= []
for row in prueba_clues.iterrows():
    rows.append(row)

#Extraer datos de tuple (quitar nombre index)
rowsf= [a_row[1] for a_row in rows]

#Extraer datos a lista
listval=[]
for lis in rowsf:
    listval.append(lis.tolist())

#Cambiar orden 
#lista de listas
flist = [list(i) for i in zip(*listval)]

#Para nombres
def hydrateCol(row, all_headers):
    hydrated = {}
    #cols = row.split("|")
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

#Lista de listas con nombres de columnas (dict)
dtaclues= hydrateCol(flist, headers)

def hydrateCol(row, all_headers):
    hydrated = {}
    cols = row
    if not len(cols):
        return False  
    for idx_head, header in enumerate(all_headers):
        try:
            hydrated[header] = cols[idx_head][idx_head]
        except Exception as e:
            print(cols)
            print(hydrated)
            return False
    return hydrated
    
    #Cambiar orden 
    #lista de listas
    #flist = [list(i) for i in zip(*listval)]
    #print(flist)



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


#Nombrar variable dentro de la lista de listas
dtaclues['FECHA ULTIMO MOVIMIENTO'] = dates_idm

####Crear variables compuestas
#total_unities
cons_gral= []
for i in dtaclues['CONSULTORIOS DE MED GRAL']:
    cons_gral.append(int(i))

dtaclues['CONSULTORIOS DE MED GRAL']=cons_gral

cons_otar= []
for i in dtaclues['CONSULTORIOS EN OTRAS AREAS']:
    cons_otar.append(int(i))

dtaclues['CONSULTORIOS EN OTRAS AREAS']=cons_otar

camas_hos= []
for i in dtaclues['CAMAS EN AREA DE HOS']:
    camas_hos.append(int(i))

dtaclues['CAMAS EN AREA DE HOS']=camas_hos

camas_otr= []
for i in dtaclues['CAMAS EN AREA DE HOS']:
    camas_otr.append(int(i))

dtaclues['CAMAS EN AREA DE HOS']=camas_otr

#total_unities final
t_uni= [cons_gral, cons_otar, camas_hos, camas_otr]
t_unid= list(map(sum, zip(*t_uni)))
dtaclues['UNIDADES TOTALES'] = t_unid

###NO SE HAN TERMINADO VARIABLES COMPUESTAS
#streat_number
dtaclues['NUMERO CALLE'] = list(map(''.join,zip(dtaclues['NUMERO EXTERIOR'],dtaclues['NUMERO INTERIOR']))) 

def streatnum(colA, colB):
    import numpy as np
    clle_num= []
    k='nan'
    a= colA
    b= colB
    for i in a:
        for j in b:
            if pd.isnull(i) and pd.isnull(j):
                return k== np.nan
            if pd.isnull(i) and not pd.isnull(j):
                return k== 'S/N' + j
            if not pd.isnull(i) and pd.isnull(i):
                return k== i
            if not pd.isnull(i) and not pd. isnull(j):
                return k== i +j
    clle_num.append(k)

            

#suburb

#

###CARGA DE INFORMACION EJEMPLO







#Prueba de carga a CLUES 
dpr = [item[0] for item in dtaclues.values()]
dprheader=dtaclues.keys()
ejmdta= hydrateCol(dpr, dprheader)

#Actualizar id para carga de ejemplo
ejmdta['ID']= 'AAABCEJEMPLO'
#https://stackoverflow.com/questions/42215526/django-create-object-if-field-not-in-database

returns = Return.objects.all()
for ret in returns:
   return_in_database = Return.objects.filter(ItemId="UUID").exists()
   if not return_in_database:
       obj, created = Return.objects.get_or_create(ItemID="UUID", 
                      ItemName="Hodaddy", State="Started")
       obj.save() 


from catalog.models import CLUES
returns = CLUES.objects.all()
for ret in returns:
    return_db = CLUES.objects.filter(name = 'AAABCEJEMPLO').exists()
    if not return_db:
        obj, created=CLUES.objects.get_or_create(
                    name=ejmdta["NOMBRE DE LA UNIDAD"],
                    #municipality - se carga field municipality? en el modelo CLUES esta
                    #municipality_inegi_code=ejmdta['CLAVE DEL MUNICIPIO'],
                    #tipology=ejmdta['NOMBRE DE TIPOLOGIA'],
                    #tipology_obj =
                    #tipology_cve=ejmdta['CLAVE DE TIPOLOGIA'],
                    #id_clues=ejmdta['ID'],
                    #clues=ejmdta['CLUES'],
                    #status_operation = ejmdta['ESTATUS DE OPERACION'],
                    #longitude=ejmdta['LONGITUD'],
                    #latitude=ejmdta['LATITUD'],
                    #locality=ejmdta['NOMBRE DE LA LOCALIDAD'],
                    #locality_inegi_code=ejmdta['CLAVE DE LA LOCALIDAD'],
                    #jurisdiction=ejmdta['NOMBRE DE LA JURISDICCION'],
                    #jurisdiction_clave=ejmdta['CLAVE DE LA JURISDICCION'],
                    #establishment_type=ejmdta['NOMBRE TIPO ESTABLECIMIENTO'],
                    #consultings_general=ejmdta['CONSULTORIOS DE MED GRAL'],
                    #consultings_other=ejmdta['CONSULTORIOS EN OTRAS AREAS'],
                    #beds_hopital=ejmdta['CAMAS EN AREA DE HOS'],
                    #beds_other=ejmdta['CAMAS EN OTRAS AREAS'],
                    #total_unities=get_int(ejmdta['UNIDADES TOTALES'], ##
                    #admin_institution=ejmdta['NOMBRE DE LA INS ADM'],
                    #atention_level=ejmdta['NIVEL ATENCION'],
                    #stratum=ejmdta['ESTRATO UNIDAD'],
                    #real_name=
                    #alter_clasif=
                    #clasif_name=
                    #prev_clasif_name=
                    #number_unity=
                    #name_in_issten=ejmdta['NOMBRE DE LA UNIDAD'],
                    #rr_data=
                    #alternative_names=
                    #type_street=ejmdta['TIPO DE VIALIDAD'],
                    #street=ejmdta['VIALIDAD'],
                    #streat_number= ejmdta['NUMERO CALLE'], ##
                    #suburb=ejmdta['SUBURBIO']
                    #postal_code=ejmdta['CODIGO POSTAL'],
                    #rfc=ejmdta['RFC DEL ESTABLECIMIENTO'],
                    #last_change=ejmdta['FECHA ULTIMO MOVIMIENTO']
                    )
        obj.save()


from catalog.models import CLUES
for i in ejmdta['FECHA ULTIMO MOVIMIENTO']:
    if i == "False":
        cluesjem= CLUES.objects.get_or_create(
                    #state=
                    #institution=
                    name=ejmdta["NOMBRE DE LA UNIDAD"],x
                    #municipality - se carga field municipality? en el modelo CLUES esta
                    #municipality_inegi_code=ejmdta['CLAVE DEL MUNICIPIO'],
                    tipology=ejmdta['NOMBRE DE TIPOLOGIA'],
                    #tipology_obj =
                    tipology_cve=ejmdta['CLAVE DE TIPOLOGIA'],
                    id_clues=ejmdta['ID'],
                    clues=ejmdta['CLUES'],
                    status_operation = ejmdta['ESTATUS DE OPERACION'],
                    longitude=ejmdta['LONGITUD'],
                    latitude=ejmdta['LATITUD'],
                    locality=ejmdta['NOMBRE DE LA LOCALIDAD'],
                    locality_inegi_code=ejmdta['CLAVE DE LA LOCALIDAD'],
                    jurisdiction=ejmdta['NOMBRE DE LA JURISDICCION'],
                    jurisdiction_clave=ejmdta['CLAVE DE LA JURISDICCION'],
                    establishment_type=ejmdta['NOMBRE TIPO DE ESTABLECIMIENTO'],
                    consultings_general=get_int(ejmdta['CONSULTORIOS DE MED GRAL']),
                    consultings_other=get_int(ejmdta['CONSULTORIOS EN OTRAS AREAS']),
                    beds_hopital=get_int(ejmdta['CAMAS EN AREA DE HOS']),
                    beds_other=get_int(ejmdta['CAMAS EN OTRAS AREAS']),
                    #total_unities=get_int(ejmdta['UNIDADES TOTALES'], ##
                    admin_institution=ejmdta['NOMBRE DE LA INS ADM'],
                    atention_level=ejmdta['NIVEL ATENCION'],
                    stratum=ejmdta['ESTRATO UNIDAD'],
                    #real_name=
                    #alter_clasif=
                    #clasif_name=
                    #prev_clasif_name=
                    #number_unity=
                    name_in_issten=ejmdta['NOMBRE DE LA UNIDAD'],
                    #rr_data=
                    #alternative_names=
                    type_street=ejmdta['TIPO DE VIALIDAD'],
                    street=ejmdta['VIALIDAD'],
                    #streat_number= ejmdta['NUMERO CALLE'], ##
                    #suburb=ejmdta['SUBURBIO']
                    postal_code=ejmdta['CODIGO POSTAL'],
                    rfc=ejmdta['RFC DEL ESTABLECIMIENTO'],
                    last_change=ejmdta['FECHA ULTIMO MOVIMIENTO']
                    )
        cluesjem.save()

#Otra prueba (field individual)
from catalog.models import CLUES
for i in ejmdta['FECHA ULTIMO MOVIMIENTO']:
    if i == "False":
        cluesjem= CLUES.objects.create(
                    #state=
                    #institution=
                    name=ejmdta["NOMBRE DE LA UNIDAD"])
        cluesjem.save()

### AQUI ME QUEDE ###

###Para todos los clues

#Para todos los CLUES
for i in dtaclues['ID']:
    for j in dtaclues['FECHA ULTIMO MOVIMIENTO']:
        if j == "True":
            CLUES.objects.get(ID = i).update(

            )


#Condicional de registro
from catalog.models import CLUES
for i in dtaclues['FECHA ULTIMO MOVIMIENTO']:
    if i == "True":
        clues = CLUES.objects.update(
                #state=
                #institution=
                name=dtaclues["NOMBRE DE LA UNIDAD"],
                #municipality - se carga field municipality? en el modelo CLUES esta
                #municipality_inegi_code=dtaclues['CLAVE DEL MUNICIPIO'],
                tipology=dtaclues['NOMBRE DE TIPOLOGIA'],
                #tipology_obj =
                tipology_cve=dtaclues['CLAVE DE TIPOLOGIA'],
                id_clues=dtaclues['ID'],
                clues=dtaclues['CLUES'],
                status_operation = dtaclues['ESTATUS DE OPERACION'],
                longitude=dtaclues['LONGITUD'],
                latitude=dtaclues['LATITUD'],
                locality=dtaclues['NOMBRE DE LA LOCALIDAD'],
                locality_inegi_code=dtaclues['CLAVE DE LA LOCALIDAD'],
                jurisdiction=dtaclues['NOMBRE DE LA JURISDICCION'],
                jurisdiction_clave=dtaclues['CLAVE DE LA JURISDICCION'],
                establishment_type=dtaclues['NOMBRE TIPO DE ESTABLECIMIENTO'],
                consultings_general=get_int(dtaclues['CONSULTORIOS DE MED GRAL']),
                consultings_other=get_int(dtaclues['CONSULTORIOS EN OTRAS AREAS']),
                beds_hopital=get_int(dtaclues['CAMAS EN AREA DE HOS']),
                beds_other=get_int(dtaclues['CAMAS EN OTRAS AREAS']),
                #total_unities=get_int(dtaclues['UNIDADES TOTALES'], ##
                admin_institution=dtaclues['NOMBRE DE LA INS ADM'],
                atention_level=dtaclues['NIVEL ATENCION'],
                stratum=dtaclues['ESTRATO UNIDAD'],
                #real_name=
                #alter_clasif=
                #clasif_name=
                #prev_clasif_name=
                #number_unity=
                name_in_issten=dtaclues['NOMBRE DE LA UNIDAD'],
                #rr_data=
                #alternative_names=
                type_street=dtaclues['TIPO DE VIALIDAD'],
                street=dtaclues['VIALIDAD'],
                #streat_number= dtaclues['NUMERO CALLE'], ##
                #suburb=dtaclues['SUBURBIO']
                postal_code=dtaclues['CODIGO POSTAL'],
                rfc=dtaclues['RFC DEL ESTABLECIMIENTO'],
                last_change=dtaclues['FECHA ULTIMO MOVIMIENTO']
                )


###PRUEBAS SENCILLAS PARA CARGAR Y ACTUALIZAR INFORMACION EN 
#Consultar un objeto
CLUES.objects.get(id=1)

#Crear un objeto
dprueba = State(inegi_code = '41',
                name ='prueba',
                short_name= 'pr', 
                code_name ='pr',
                other_names = 'P' )
dprueba.save()

#Actualizar un objeto
State.objects.filter(inegi_code='40').update(inegi_code='98')
#Eliminar un objeto
State.objects.filter(inegi_code ='98').delete()

#Diccionario


from catalog.models import State
states = State.objects.all()
for state in states:
    try:
        new_state = State.objects.get(inegi_code='40').exists()
    except:
        new_state, created = State.objects.get_or_create(inegi_code = '40',
                                                    name = 'prueba',
                                                    short_name = 'pr', 
                                                    code_name = 'pr',
                                                    other_names = 'P')
    new_state.save() 







##PEQUEÑA FUNCION PARA IDENTIFICAR LOS MOVIMIENTOS DESPUES DEL 2019-12-31
def is_new_mov():
    import pandas as pd
    from datetime import date
    path_excel = 'D:\\Documents\\desabasto_ocamis\\pruebas_scripts\\prueba_clues.xlsx'
    prueba_clues = pd.read_excel(path_excel, dtype = 'string', nrows=50)
    date_mod = prueba_clues['FECHA ULTIMO MOVIMIENTO'].array
    dates_idm =[]
    datet = date.fromisoformat('2019-12-31')
    for i in date_mod:
        #datesm.append(date.fromisoformat(i)) 
        if (date.fromisoformat(i)) > datet: 
            dates_idm.append("True")
        else:
            dates_idm.append("False")
    print(dates_idm)





#########FUNCIONES Y TODO LO DEMAS DE APOYO 




#Ejemplo de funcion para cargar txt
from array import array
import string
from tkinter import N
from wsgiref.handlers import read_environ
from wsgiref.validate import IteratorWrapper
from xmlrpc.client import DateTime


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

#Prueba 1: 19/07/2022
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
###DUDAS DE LA FUNCION DE PRUEBA:
#a los excel no se les define por medio de funcion el total de columanas, las columnas se generan de manera automatica en la


##Prueba 1: 21/07/2022 
###Pruebas para cargar CLUES con nuevos campos en formato 
#Los campos nuevos de la base clues ya se definieron en el catalogo CLUES pero falta verificar los que ocupan creacion con dos campos 
# (streat_number and suburb)
def import_clues_p():
    import pandas as pd
    import unidecode
    #from pprint import pprint  #visualice the data with more structure
    from django.utils.dateparse import parse_datetime #parse_datime converts text to a datetime with time
    from catalog.models import (State, Institution, CLUES)
    #with pd.read_excel('D:\\Documents\\desabasto_ocamis\\pruebas_scripts\\prueba_clues.xlsx') as prueba_clues:
    prueba_clues = pd.read_excel('D:\\Documents\\desabasto_ocamis\\pruebas_scripts\\prueba_clues.xlsx', dtype ="string") ###
    prueba_clues['ID'].isna().sum() #No hay NAs ###
    prueba_clues['NOMBRE DE LA UNIDAD'].isna().sum() #No hay NAs ###
    #El comando .astype(str) convierte a str 
    prueba_clues['ID_PRUEBA'] = prueba_clues['ID'] +'_'+ prueba_clues['NOMBRE DE LA UNIDAD'] ###
    #d= {'ID_PRUEBA' : [prueba_clues['ID'].astype(str) +'_'+ prueba_clues['NOMBRE DE LA UNIDAD']]}
    #prueba_clues = prueba_clues.append(pd.DataFrame(d))
    #prueba_clues['ID_PRUEBA'] = pd.(ID_PRUEBA)
        #the next command create a nested dictionary (a dictionary of dictionaries)
        reader_clues = prueba_clues.set_index('ID_PRUEBA').to_dict('index') #Se hace al NOMBRE DE LA UNIDAD el index ###
        #https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_dict.html
        try:
            reader_clues.index = unidecode.unidecode(reader_clues.index).upper() #str en lugar de unicode#checar
        except Exception:
            reader_clues.index = reader_clues.upper()
        #Como se hace la importacion?
        ##llamar a catalogos para las fK
        ##no es necesario para la importacion mayusculas unidecode
        try:
            state = State.objects.get(inegi_code = reader_clues['CLAVE DE LA ENTIDAD']) #Se llama al catalogo State
            institution = Institution.objects.get(code = reader_clues['CLAVE DE LA INSTITUCION']) #Se llama al catalogo Institutions (nomenclatura de instituciones)
        except Exception as exc:
            state = None
            institution = None
            ##Crear (importar datos a modelo CLUEs)
        print()    
        print(reader_clues)
        clues = CLUES.objects.create()
        #el index aqui es el NOMBRE DE LA UNIDADAD y cada unidad tiene un field. Como llamo a todos los field uno a uno (for) para caragarlos en el field correspondiente?
            name = reader_clues.index
            for c_unidad, c_info in reader_clues.items():
                for key in c_info:
                    for tfield in CLUES.objects.all():
                        key = tfield  #Estos tres for funcionarian si el archivo original CLUES de excel tiene el mismo orden que los field de modelo CLUES
        ) #las variables del archivo de excel de CLUES no tienen el mismo orden por lo que se debe llamar a una o acomodar en la funcion
        print(clues)

##
#Prueba 2:24/07/22
###Pruebas para cargar CLUES con nuevos campos en formato 
def import_clues_p01():
    import pandas as pd
    import unidecode
    #from pprint import pprint  #visualice the data with more structure
    #parse_datime converts text to a datetime with time
    from django.utils.dateparse import parse_datetime 
    from catalog.models import (State, Institution, CLUES)
    #Se carga archivo xlsx y desde el comienzo todas se declaran string para prueba
    #se puede asignar el datatype de cada variable con el comand pd.read_excel
    prueba_clues = pd.read_excel('D:\\Documents\\desabasto_ocamis\\pruebas_scripts\\prueba_clues.xlsx', dtype ="string", nrows= 50)
    prueba_clues.items()
    #Se crea nuevo item en diccionario para asigarlo como index
    prueba_clues['ID_PRUEBA'] = prueba_clues['ID'] +'_'+ prueba_clues['NOMBRE DE LA UNIDAD']
    #el siguiente comando ayuda a asignar como index el item creado
    #se crea un nested dictionary (a dictionary of dictionaries)
    #no se usa comando de linea 169 porque sale error al llamarlo dentro de los loops
    #reader_clues = prueba_clues.set_index('ID_PRUEBA').to_dict('index')
    #Se crean listas con los elementos del diccionario prueba clues
    pr_st= list(prueba_clues['CLAVE DE LA ENTIDAD'])
    pr_inst = list(prueba_clues['CLAVE DE LA INSTITUCION'])
    #Se itera la lista pr_st y se llama a los objetos del modelo State
    try:
        for st in pr_st:
            state = State.objects.get(inegi_code = row)
    except Exception as e:
        state = None
        print(pr_st)
    #Se itera lista de las claves de la institucion 

    for inst in pr_inst:
        try:
            institution = Institution.objects.get(code = inst)
        except Exception as e:
            institution = None
    #Prueba para iterar con diccionario
    for elem in prueba_clues["NOMBRE DE LA UNIDAD"]:
        #En esta iteracion sale un error porque falla la restriccion de no nulo
        try:
            clues = CLUES.objects.create(
                name=elem)
        except Exception as e:
            institution = None
            print(e)
    
IteratorWrapperarray
    ##Comentarios sobre los elemetos del modelo CLUES:
    for elem in prueba_clues.values():
        clues = CLUES.objects.create(
                    state=state,
                    #institution field viene de 'CLAVE DE LA INSTITUCION'
                    institution=institution,
                    name=prueba_clues["NOMBRE DE LA UNIDAD"],
                    #is_searchable 
                    #municipality - se carga field municipality? en el modelo CLUES esta
                    municipality_inegi_code=prueba_clues['CLAVE DEL MUNICIPIO'],
                    tipology=prueba_clues['NOMBRE DE TIPOLOGIA'],
                    #tipology_obj - field en modelo clues que no esta en la base
                    tipology_cve=prueba_clues['CLAVE DE TIPOLOGIA'],
                    id_clues=prueba_clues['ID'],
                    clues=prueba_clues['CLUES'],
                    #status operation -
                    longitude=prueba_clues['LONGITUD'],
                    latitude=prueba_clues['LATITUD'],
                    locality=prueba_clues['NOMBRE DE LA LOCALIDAD'],
                    locality_inegi_code=prueba_clues['CLAVE DE LA LOCALIDAD'],
                    jurisdiction=prueba_clues['NOMBRE DE LA JURISDICCION'],
                    jurisdiction_clave=prueba_clues['CLAVE DE LA JURISDICCION'],
                    establishment_type=prueba_clues['NOMBRE TIPO DE ESTABLECIMIENTO'],
                    consultings_general=get_int(prueba_clues['CONSULTORIOS DE MED GRAL']),
                    consultings_other=get_int(prueba_clues['CONSULTORIOS EN OTRAS AREAS']),
                    beds_hopital=get_int(prueba_clues['CAMAS EN AREA DE HOS']),
                    beds_other=get_int(prueba_clues['CAMAS EN OTRAS AREAS']),
                    total_unities=get_int(prueba_clues['CAMAS EN AREA DE HOS']) + get_int(prueba_clues['CAMAS EN OTRAS AREAS']),
                    admin_institution=prueba_clues['NOMBRE DE LA INS ADM'],
                    atention_level=prueba_clues['NIVEL ATENCION'],
                    stratum=prueba_clues['ESTRATO UNIDAD'],
                    #real_name 
                    #alter_clasif
                    #clasif_name
                    #prev_clasif_name
                    #number_unity -cual es el numero de la unidad en la base?
                    #FALTA POR INTEGRAR EN EL CLUES:
                    #NOMBRE DE LA INSTTITUCION? o no es necesario por que esta en el modelo institutions
                    #TIPO DE VIALIDAD
                    #VIALIDAD
                    #NUMERO INTERIOR 
                    #NUMERO EXTERIOR
                    #TIPO DE ASENTAMIETO
                    #ASENTAMIENTO
                    #CODIGO POSTAL
                    #ESTATUS DE OPERACION?
                    #RFC DEL ESTABLECIMIENTO
                    #FECHA ULTIMO MOVIMIENTO
                )
                print(clues)

#CODIGOS PARA REVISION 
#Se obtienen una lista de los nombres de las variables del excel
var_names = [name for name in prueba_clues]
#SE obtiene una lista de los nombres de los field de CLUES 
#Este comando trae toda la información del model de django
#se pueden extraer los nombres por medio de expresiones regulares
clues_fiel = str([field for field in CLUES._meta.fields])


###27/07/2022
##FUNCION PARA IDENTIFICAR LOS MOVIMIENTOS DESPUES DEL 2019-12-31
def is_new_mov():
    import pandas as pd
    from datetime import date
    path_excel = 'D:\\Documents\\desabasto_ocamis\\pruebas_scripts\\prueba_clues.xlsx'
    prueba_clues = pd.read_excel(path_excel, dtype = 'string', nrows=50)
    date_mod = prueba_clues['FECHA ULTIMO MOVIMIENTO'].array
    dates_idm =[]
    datet = date.fromisoformat('2019-12-31')
    for i in date_mod:
        #datesm.append(date.fromisoformat(i)) 
        if (date.fromisoformat(i)) > datet: 
            dates_idm.append("True")
        else:
            dates_idm.append("False")
    print(dates_idm)


##Cachos para crear funcion
##Carga de CLUES en formato xlsx
path_excel = 'D:\\Documents\\desabasto_ocamis\\pruebas_scripts\\prueba_clues.xlsx'
prueba_clues = pd.read_excel(path_excel, dtype ="string", nrows= 50)
headers = prueba_clues.keys().array
prueba_clues.items()

for row in prueba_clues.iterrows():
    print(row)


#Funcion para sumar campos
#Funcion para concatenar campos

#Extraer valores de df
#df= rowsf[0].rename(None).to_frame().T

#loop para obtener names of dictionary
#por ahora solo imprime los nombres de los objetos del dictionary prueba_clues
#var_names = []
#for name in prueba_clues:
#    var_names.append(name)

#Codigo (en construccion) para obtener model's fields in Django
#https://stackoverflow.com/questions/3647805/get-models-fields-in-django
#El siguiente
#from django.contrib.auth.models import User
#User._meta.get_fields()
#[field.name for field in User._meta.get_fields()]

#from django.utils.dateparse import parse_datetime 
#from catalog.models import (State, Institution, CLUES)

#    try:
#       for row in pr_st:
#           state = State.objects.get(inegi_code = row)
#   except Exception as e:
#       state = None
#    str_clues = []
#   for elem in clues_fiel:
#       str_clues.append = str(elem)
#   elem_clues_fiel = [sub for sub in clues_fiel ]
#for field in CLUES._meta.fields:
#   print(field.name)


#Funcion de ejemplo:
def import_clues():
    import csv
    from pprint import pprint
    from django.utils.dateparse import parse_datetime
    from desabasto.models import (State, Institution, CLUES)
    with open('D:\\Documents\\desabasto_ocamis\\pruebas_scripts\\clues.csv') as csv_file:
        #contents = f.read().decode("UTF-8")
        #csv_reader = csv.reader('D:\\Documents\\desabasto_ocamis\\pruebas_scripts\\clues.csv', delimiter=',')
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for idx, row in enumerate(csv_reader):
            row = [item.decode('latin-1').encode("utf-8") for item in row]
            if not len(row) == 25:
                print("No coincide el número de columnas, hay %s" % len(row))
                print("linea: %s"%idx+1)
                print(row)
                print("----------")
                continue
            if line_count <= 1:
                continue
            else:
                state_inegi_code = row[1]
                try:
                    state = State.objects.get(inegi_code=state_inegi_code)
                except Exception as e:
                    state = None
                institution_clave = row[2]
                institution = Institution.objects.get(code=institution_clave)
                clues = CLUES.objects.create(
                    name=row[0],
                    state=state,
                    institution=institution,
                    municipality=row[3],
                    municipality_inegi_code=row[4],
                    tipology=row[5],
                    tipology_cve=row[6],
                    id_clues=row[7],
                    clues=row[8],
                    status_operation=row[9],
                    longitude=row[10],
                    latitude=row[11],
                    locality=row[12],
                    locality_inegi_code=row[13],
                    jurisdiction=row[14],
                    jurisdiction_clave=row[15],
                    establishment_type=row[16],
                    consultings_general=get_int(row[17]),
                    consultings_other=get_int(row[18]),
                    beds_hopital=get_int(row[19]),
                    beds_other=get_int(row[20]),
                    total_unities=get_int(row[21]),
                    admin_institution=row[22],
                    atention_level=row[23],
                    stratum=row[24],
                )
                print(clues)



import pandas as pd
import unidecode

from django.utils.dateparse import parse_datetime #parse_datime converts text to a datetime with time
from catalog.models import (State, Institution, CLUES)


for idx, row in enumerate(csv_reader):
    row = [item.decode('latin-1').encode("utf-8") for item in row]

for idx, row in d:
    row = [item.decode('latin-1').encode("utf-8") for item in row]
    if not len(row) == 25:
        print("No coincide el número de columnas, hay %s" % len(row))
        print("linea: %s"%idx+1)
        print(row)
        print("----------")
        continue
    if line_count <= 1:
        continue
    else:
        state_inegi_code = row[1]
        try:
            state = State.objects.get(inegi_code=state_inegi_code)
        except Exception as e:
            state = None



##Pruebas no usadas
'''
##Pruebas 25/07/22
with open(path) as f:
        reader = csv.reader(f)
        for row in reader:
            created = Teacher.objects.get_or_create(
                first_name=row[0],
                last_name=row[1],
                middle_name=row[2],
                )
            # creates a tuple of the new object or
            # current object and a boolean of if it was created


#CELDAS CODIGO PARA QUITAR VACIAS EN EXCEL:
#data= pd.read_excel(io=one_path)
with open(data) as frows:  #Era para contar el numero de filas vacías
empty_row= sum(line.isspace() for line in f) #Esto era para contar las filas vacias '''

#Prueba
#Carga de varios archivos de Excel de manera automatizada
#Esta parte se puede hacer una funcion para caragar todo de manera automatizada
one_path= #direcciones donde se encuntran los archivos
mes= #lista de meses
from catalog.models import Delegation
from files_rows.models import GroupFile
from parameter.models import TypeData #obtencion del nombre de la delagacion, el cual esta contenido en el nombre del archivo
    deleg_nom = Delegation.objects.filter(name=name).first()

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


def ejemplo()
    path_excel = 'G:\\Mi unidad\\YEEKO\\Proyectos\\OCAMIS\\Ejercicios Itza\\prueba_clues.xlsx'
    prueba_clues = pd.read_excel(path_excel, dtype ="string", nrows= 50)
    
    headers
    #for row in prueba_clues.iterrows():
    all_rows = [["34", "IMSS"], ]

    def is_new(update_date):
        if update_date


    for row in all_rows:
        index = row[0]
        data_row = row[1].array
        data_dict = hydrateCol(data_row, headers)
        #CHECAR LA FUNCIÓN .split() POR CADA ELEMENTO.
        #FALTA COMPROBAR SI YA EXISTA, PARA NO CREARLO, EN SU CASO USAR .update()
        print(clues)
        create_clues(row)

###
#Importar diccionarios

#TESTEAR ANTES
#dummy_row = {""}
#create_clues(dummy_row)

