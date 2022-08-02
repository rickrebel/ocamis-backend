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


#funcion de carga de Excel (solo listas sin nombres)
path_excel = 'D:\\Documents\\desabasto_ocamis\\pruebas_scripts\\prueba_clues.xlsx'
def import_excelnh(path_excel):
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
    return(listval)


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




#Con nombres de variables CLUES
ejmdta=listval
from catalog.models import CLUES, Institution
alldata = CLUES.objects.all()
for dat in alldata:
    alldata_db = CLUES.objects.filter(name = "listval[17]").exists()
    if not return_db:
        obj, created=CLUES.objects.get_or_create(
                    name=ejmdta["NOMBRE DE LA UNIDAD"],
                    municipality - se carga field municipality? en el modelo CLUES esta
                    municipality_inegi_code=ejmdta['CLAVE DEL MUNICIPIO'],
                    tipology=ejmdta['NOMBRE DE TIPOLOGIA'],
                    tipology_obj =
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
                    establishment_type=ejmdta['NOMBRE TIPO ESTABLECIMIENTO'],
                    consultings_general=ejmdta['CONSULTORIOS DE MED GRAL'],
                    consultings_other=ejmdta['CONSULTORIOS EN OTRAS AREAS'],
                    beds_hopital=ejmdta['CAMAS EN AREA DE HOS'],
                    beds_other=ejmdta['CAMAS EN OTRAS AREAS'],
                    total_unities=ejmdta['UNIDADES TOTALES'], 
                    admin_institution=ejmdta['NOMBRE DE LA INS ADM'],
                    atention_level=ejmdta['NIVEL ATENCION'],
                    stratum=ejmdta['ESTRATO UNIDAD'],
                    real_name=
                    alter_clasif=
                    clasif_name=
                    prev_clasif_name=
                    number_unity=
                    name_in_issten=ejmdta['NOMBRE DE LA UNIDAD'],
                    rr_data=
                    alternative_names=
                    type_street=ejmdta['TIPO DE VIALIDAD'],
                    street=ejmdta['VIALIDAD'],
                    streat_number= ejmdta['NUMERO CALLE'], 
                    suburb=ejmdta['SUBURBIO']
                    postal_code=ejmdta['CODIGO POSTAL'],
                    rfc=ejmdta['RFC DEL ESTABLECIMIENTO'],
                    last_change=ejmdta['FECHA ULTIMO MOVIMIENTO']
                    )
        obj.save()


###Consultas CLUES

from catalog.models import CLUES
from catalog.models import Institution
from django.db.models import Count, Sum, Max, Min, Avg
from django.db.models import F, Q, When, FilteredRelation

#Total clues por institución
totalclu = CLUES.objects.all().values(
    'institution').annotate(total_clues = Count('institution')).order_by('-total_clues')
print(totalclu)
#Comentario: Model Institution no está activo

#Cuantas clues hay activas
activclue = CLUES.objects.all().values(
    'status_operation').annotate(status_clues = Count('status_operation')).order_by('-status_clues')
print(activclue)

#De que tamaño son las umaes del imss
#a partir de sus camas y consultorios
path_excel = 'D:\\Documents\\desabasto_ocamis\\umaes_imss.xlsx'
umaes = import_excelnh(path_excel)
cluesumae = [umae[0] for umae in umaes]
tam_umaes= CLUES.objects.filter(
        clues__in = cluesumae).values('clues', 'beds_hopital',
        'beds_other','consultings_general','consultings_other')
print(tam_umaes)

#Maximo de camas de hospital de las umaes del imss
maxbed_umae = list(tam_umaes.aggregate(Max('beds_hopital')).values())
maxbed_umae = float(maxbed_umae[0])

#Minimo de camas de hospital de las umaes de imss
minbed_umae = list(tam_umaes.aggregate(Min('beds_hopital')).values())
minbed_umae = float(minbed_umae[0])

#Estratificacion por tamaño
#Clues estratificadas segun numero maximo y minimo de camas de las umaes imss
estrati_clue = CLUES.objects.aggregate(
        large = Count('clues', 
                    filter = Q(beds_hopital__gte = maxbed_umae)), #mayor o igual que
        medium = Count('clues', 
                    filter = Q(beds_hopital__gte = minbed_umae, beds_hopital__lte=maxbed_umae)),
        small = Count('clues', 
                    filter = Q(beds_hopital__lte=63))
    )
print(estrati_clue)

#Clues que contienen en su nombre "de alta especialidad"
clues_aesp = CLUES.objects.filter(name__icontains='DE ALTA ESPECIALIDAD')
print(clues_aesp)

#Estatus de operacion del total de instituciones
status_clues = CLUES.objects.values(
    'institution','status_operation').annotate(
        status_clues = Count('status_operation')).order_by('institution')
print(status_clues)





