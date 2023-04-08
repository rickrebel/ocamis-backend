#Funcion para nombres de columnas
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
    prueba_clues = pd.read_excel(path_excel, dtype = 'string')
    #Nombres de columnas (pandaarray)
    #headers = prueba_clues.keys().array
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

#Para probar funcion import_excelnh
dataxl = import_excelnh(path_excel)


#Funcion para identificar clues nuevos/actualizados
def date_act(datalist):
    import pandas as pd
    from datetime import datetime
    listfilt = {}
    dates_idm = ()
    datet = datetime.strptime('2019-12-31', '%Y-%m-%d').date()
    for datee in datalist:
        try:
            dat = datetime.strptime(datee[32], '%Y-%m-%d').date()
        except:
            dat = pd.NaT
        if pd.isnull(dat):
            datee.append("NA")
        if not dat > datet: 
            datee.append("False")
        else:
            datee.append("True")
        dates_idm = (*dates_idm, datee)
    return(dates_idm)

#Para probar funcion datalist
datalist = dataxl


#Funcion para identificar clues nuevas
def new_clues(tot_list):
    import pandas as pd
    from geo.models import CLUES
    new_clue = ()
    old_clue = list(CLUES.objects.values_list('clues', flat=True))
    for row in tot_list:
        if row[1] in old_clue:
            row.append("False")
        if row[1] not in old_clue:
            row.append("True")
        new_clue = (*new_clue, row)
    return(new_clue)

#Para probar funcion new_clues
news_clues = new_clues(tot_list)


# Funcion para cargar clues nuevas identificadas con new_clues
# Esta funcion se está probando...
def import_new_clues(tot_list):
    from geo.models import State
    from geo.models import Institution
    from geo.models import CLUES
    from geo.models import Municipality
    new_clues = tot_list
    # new_clues = new_clues(tot_list)
    for row in new_clues:
        state_inegi_code = row[2]
        try:
            state = State.objects.get(inegi_code=state_inegi_code)
        except Exception as e:
            state = None
        print(state)
        institution_clave = row[9]
        try:
            institution = Institution.objects.get(code=institution_clave)
        except Exception as e:
            institution = None
        municipality_inegi_code = row[3]
        try:
            municipality = Municipality.objects.get(inegi_code=municipality_inegi_code)
        except Exception as e:
            municipality = None    
        clues_n = CLUES.objects.create(
            state=state,
            institution=institution,
            name=row[17],
            #municipality - se carga field municipality? en el modelo CLUES esta
            municipality_inegi_code = municipality,
            typology = row[11],
            #typology_obj =
            typology_cve=row[12],
            id_clues=row[0],
            clues=row[1],
            status_operation=row[25],
            longitude=row[28],
            latitude=row[27],
            locality=row[4],
            locality_inegi_code=row[5],
            jurisdiction=row[6],
            jurisdiction_clave=row[7],
            establishment_type=row[10],
            consultings_general=row[13],
            consultings_other=row[14],
            beds_hopital=row[15],
            beds_other=row[16],
            #total_unities=row['UNIDADES TOTALES'], 
            admin_institution=row[29],
            atention_level=row[30],
            stratum=row[31],
            #real_name=
            #alter_clasif=
            #clasif_name=
            #prev_clasif_name=
            #number_unity=
            name_in_issten=row[17],
            #rr_data=
            #alternative_names=
            type_street=row[18],
            street=row[19],
            #streat_number= row['NUMERO CALLE'], 
            #suburb=row['SUBURBIO']
            postal_code=row[24],
            rfc=row[26],
            #last_change=row[32]
        )
        print(clues_n)


#Para hacer pruebas de carga a clues
#Ejemplo para carga clues
ejemplo = (['01']*43, ['02']*43)
ejemplo[0][9] = 1
ejemplo[1][9] = 2
ejemplo[0][3] = '001'
ejemplo[1][3] = '002'
tot_list = ejemplo




###ANALISIS DE DATOS
###Consultas CLUES

from geo.models import CLUES
from geo.models import Institution
from django.db.models import Count, Sum, Max, Min, Avg
from django.db.models import F, Q, When, FilteredRelation

#Total clues por institución
totalclu = CLUES.objects.all().values(
    'institution').annotate(total_clues = Count('institution')).order_by('-total_clues')
print(totalclu)
#Comentario: Model Institution no está activo

#Total de clues del IMSS
totalcluIMSS = CLUES.objects.filter(institution__code='IMSS').values(
    'institution').annotate(total_clues = Count('institution'))
print(totalcluIMSS)


#Cuantas clues hay activas
activclue = CLUES.objects.all().values(
    'status_operation').annotate(status_clues = Count('status_operation')).order_by('-status_clues')
print(activclue)

#De que tamaño son las umaes del imss (arcivo umaes)
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





