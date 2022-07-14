from desabasto.models import *
import re
from django.db.models import Q
import unidecode


def import_clues():
    import csv
    from pprint import pprint
    from django.utils.dateparse import parse_datetime
    from desabasto.models import (State, Institution, CLUES)
    with open('clues.csv') as csv_file:
        #contents = f.read().decode("UTF-8")
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            row=[item.decode('latin-1').encode("utf-8") for item in row]
            if not len(row) == 25:
                print("linea: %s"%line_count)
                print(len(row))
                continue
            if line_count in [0,1]:
                line_count += 1
                continue
            else:
                line_count += 1
                state_inegi_code=row[1]
                try:
                    state=State.objects.get(inegi_code=state_inegi_code)
                except Exception as e:
                    state=None
                institution_clave=row[2]
                institution=Institution.objects.get(code=institution_clave)
                clues=CLUES.objects.create(
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
                    consultings_general=int(row[17]) if row[17].isdigit() else 0,
                    consultings_other=int(row[18]) if row[18].isdigit() else 0,
                    beds_hopital=int(row[19]) if row[19].isdigit() else 0,
                    beds_other=int(row[20]) if row[20].isdigit() else 0,
                    total_unities=int(row[21]) if row[21].isdigit() else 0,
                    admin_institution=row[22],
                    atention_level=row[23],
                    stratum=row[24],
                )
                print(clues)


def update_institution_public():
    from desabasto.models import Institution
    for institution in Institution.objects.all():
        institution.public_name=institution.name
        institution.public_code=institution.code
        institution.save()


def set_searcheable_clues():
    from desabasto.models import (State, Institution, CLUES)
    from django.db.models import Q
    is_seach = CLUES.objects.filter(status_operation='EN OPERACION')\
        .exclude(Q(institution__code='SMP')|Q(institution__code='HUN')
            |Q(institution__code='CIJ')|Q(institution__code='CRO')
            |Q(establishment_type='DE APOYO')
            |Q(establishment_type='DE ASISTENCIA SOCIAL')
            |Q(tipology_cve='BS')|Q(tipology_cve='X')
            |Q(tipology_cve='P')|Q(tipology_cve='UMM'))
    is_seach.update(is_searchable=True)


tipologies = [{
    'tipology_cve': u'UMF',
    'tipology': None,
    'tipologies': None,
    'all_clues': True,
    'prev_clasif_name': u'UMF',
    'clasif_name': u'Unidad Médica Familiar',
    'alter_clasifs': u'unidad de medicina familiar',
    'chars':[u'UMF ', u'Unidad de Medicina Familiar No. '
        ,u'Unidad de Medicina Familiar No.',u'Unidad de Medicina Familiar ',
        u'UMF No',u'U.H.F. ',u'UMF/UMAA '],
},{
    'tipology_cve': None,
    'tipology': u'CASA DE SALUD',
    'tipologies': None,
    'all_clues': True,
    'prev_clasif_name': u'Casa de S.',
    'clasif_name': u'Casa de Salud',
    'alter_clasifs': u'',
    'chars':[u'Casa de salud '],
},{
    'tipology_cve': None,
    'tipology': u'CLÍNICA DE ESPECIALIDADES',
    'tipologies': None,
    'all_clues': False,
    'prev_clasif_name': u'Clínica de Esp.',
    'clasif_name': u'Clínica de Especialidades',
    'alter_clasifs': None,
    'chars':[u'CE '],
},{
    'tipology_cve': u'99',
    'tipology': None,
    'tipologies': None,
    'all_clues': False,
    'prev_clasif_name': u'CRI',
    'clasif_name': u'Centro de Rehabilitación Integral',
    'alter_clasifs': u'educación especial',
    'chars':[
        u'CENTRO DE REHABILITACION INTEGRAL (CRI)',
        u'CENTRO DE REHABILITACION INTEGRAL ',
        u'CENTRO DE REHABILITACION Y EDUCACION ESPECIAL '],
},{
    'tipology_cve': u'CAAPS',
    'tipology': None,
    'tipologies': None,
    'all_clues': True,
    'prev_clasif_name': u'CAAPS',
    'clasif_name': u'Centro de Rehabilitación Integral',
    'alter_clasifs': u'ceaps ceap cap cedral caap',
    'chars':[u'CAAPS ',u'CEAPS ','CENTRO DE SALUD CEDRAL','CENTRO DE SALUD ',
        u'CENTRO AVANZADO DE ATENCIÓN PRIMARIA A LA  SALUD',
        u'CENTRO AVANZADO DE ATENCIÓN PRIMARÍA A LA SALUD',
        u'CENTRO ESPECIALIZADO EN ATENCIÓN PRIMARIA A LA SALUD'],
},{
    'tipology_cve': None,
    'tipology': u'CENTRO DE SALUD CON HOSPITALIZACIÓN',
    'tipologies': None,
    'all_clues': True,
    'prev_clasif_name': u'CS c/Hosp',
    'clasif_name': u'C. de Salud con Hospitalización',
    'alter_clasifs': u'clínica regional',
    'chars':[
        u'CENTRO DE SALUD CON HOSPITALIZACIÓN',
        u'CENTRO DE SALUD CON HOSPITAL',
        u'C.S. C/ HOSPITALIZACIÓN'
        u'CSC/H '
        u'CLINICA REGIONAL'
    ],
},{
    'tipology_cve': None,
    'tipology': u'CENTROS DE SALUD CON SERVICIOS AMPLIADOS',
    'tipologies': None,
    'all_clues': True,
    'prev_clasif_name': u'CESSA',
    'clasif_name': u'C. de Salud con Serv. Ampliados',
    'alter_clasifs': u'cesa',
    'chars':[
        u'CENTRO DE SALUD DE SERVICIOS AMPLIADOS DE',
        u'CENTRO DE SALUD CON SERVICIOS AMPLIADOS (CESSA)',
        u'CENTRO DE SALUD CON SERVICIOS AMPLIADOS',
        u'CENTRO DE SALUD',
        u'CESSA',
        u'CESA'
    ],
},
{
    'tipology_cve': None,
    'tipology': u'HOSPITAL ESPECIALIZADO',
    'tipologies': None,
    'all_clues': False,
    'prev_clasif_name': u'H Esp',
    'clasif_name': u'Hospital Especializado',
    'alter_clasifs': 'especialidades',
    'chars':[
        u'HIES',
    ],
},{
    'tipology_cve': None,
    'tipology': u'HOSPITAL ESPECIALIZADO',
    'tipologies': None,
    'all_clues': False,
    'prev_clasif_name': u'H Ped',
    'clasif_name': u'Hospital Pediátrico',
    'alter_clasifs': 'pediatría',
    'chars':[
        u'HOSPITAL PEDIÁTRICO',
    ],
},{
    'tipology_cve': None,
    'tipology': u'HOSPITAL ESPECIALIZADO',
    'tipologies': None,
    'all_clues': False,
    'prev_clasif_name': u'H Mat-Inf',
    'clasif_name': u'Hospital Materno Infantil',
    'alter_clasifs': 'pediatría',
    'chars':[
        u'HOSPITAL MATERNO INFANTIL',
    ],
},{
    'tipology_cve': None,
    'tipology': u'HOSPITAL ESPECIALIZADO',
    'tipologies': None,
    'all_clues': False,
    'prev_clasif_name': u'H Mujer',
    'clasif_name': u'Hospital de la Mujer',
    'alter_clasifs': None,
    'chars':[
        u'HOSPITAL DE LA MUJER',
    ],
},{
    'tipology_cve': None,
    'tipology': u'HOSPITAL ESPECIALIZADO',
    'tipologies': None,
    'all_clues': False,
    'prev_clasif_name': u'HRAE Mujer',
    'clasif_name': u'Hosp. Reg. de Alta Espec. de la Mujer',
    'alter_clasifs': 'especialidad hospital regional',
    'chars':[
        u'HOSPITAL REGIONAL DE ALTA ESPECIALIDAD DE LA MUJER',
    ],
},{
    'tipology_cve': None,
    'tipology': u'HOSPITAL ESPECIALIZADO',
    'tipologies': None,
    'all_clues': False,
    'prev_clasif_name': u'HRAE',
    'clasif_name': u'Hosp. Reg. de Alta Especialidad',
    'alter_clasifs': 'hospital regional',
    'chars':[
        u'HOSPITAL REGIONAL DE ALTA ESPECIALIDAD',
    ],
},{
    #CAMBIO
    'tipology_cve': None,
    'tipology': u'HOSPITAL DE GINECO-PEDIATRÍA',
    'tipologies': None,
    'all_clues': True,
    'prev_clasif_name': u'H Esp',
    'clasif_name': u'Hospital de Ginecopediatría',
    'alter_clasifs': 'especialidades',
    'chars':[
        u'HGP',
    ],
},{
    'tipology_cve': None,
    'tipology': u'HOSPITAL DE GINECO-OBSTETRICIA',
    'tipologies': None,
    'all_clues': True,
    'prev_clasif_name': u'HGO',
    'clasif_name': u'Hospital de Gineco Obstetricia',
    'alter_clasifs': 'ginecológico',
    'chars':[
        u'HGO',
    ],
},{
    'tipology_cve': None,
    'tipology': u'HOSPITAL DE GINECO-OBSTETRICIA CON MEDICINA FAMILIAR',
    'tipologies': None,
    'all_clues': True,
    'prev_clasif_name': u'HGOMF',
    'clasif_name': u'H. de Gineco-Obstetricia con Med. Fam.',
    'alter_clasifs': 'ginecologico medicina familiar hospital',
    'chars':[
        u'HGOMF',
    ],
},{
    'tipology_cve': None,
    'tipology': u'HOSPITAL GENERAL DE SUBZONA',
    'tipologies': None,
    'all_clues': True,
    'prev_clasif_name': u'HGSZ',
    'clasif_name': u'Hospital Gral de Subzona',
    'alter_clasifs': 'general subzona',
    'chars':[
        u'HGS',
    ],
},{
    'tipology_cve': None,
    'tipology': u'HOSPITAL GENERAL DE SUBZONA CON MEDICINA FAMILIAR',
    'tipologies': None,
    'all_clues': True,
    'prev_clasif_name': u'HRAE Mujer',
    'clasif_name': u'Hosp Gral de Subzona con Med Fam',
    'alter_clasifs': ' HOSPITAL GENERAL MEDICINA FAMILIAR',
    'chars':[
        u'HGSMF',
    ],
},{
    'tipology_cve': None,
    'tipology': u'HOSPITAL DE ESPECIALIDADES',
    'tipologies': None,
    'all_clues': True,
    'prev_clasif_name': u'HE',
    'clasif_name': u'Hospital de Especialidades',
    'alter_clasifs': None,
    'chars':[
        u'HES',
    ],
},{
    'tipology_cve': None,
    'tipology': u'HOSPITAL PSIQUIÁTRICO',
    'tipologies': None,
    'all_clues': True,
    'prev_clasif_name': u'H Psiq',
    'clasif_name': u'Hospital Psiquiátrico',
    'alter_clasifs': 'psiquiatra',
    'chars':[
        u'HOSPITAL PSIQUIÁTRICO',
    ],
},{
    'tipology_cve': None,
    'tipology': u'HOSPITAL GENERAL REGIONAL',
    'tipologies': None,
    'all_clues': True,
    'prev_clasif_name': u'HGR',
    'clasif_name': u'Hospital General Regional',
    'alter_clasifs': u'',
    'chars':[
        u'HGR',
        u'HOSPITAL GENERAL REGIONAL',
    ],
},
{
    'tipology_cve': None,
    'tipology': u'HOSPITAL GENERAL DE ZONA CON MEDICINA FAMILIAR',
    'tipologies': None,
    'all_clues': True,
    'prev_clasif_name': u'HGZMF',
    'clasif_name': u'Hosp Gral de Zona con Med Fam',
    'alter_clasifs': u'Hospital General de Medicina Familiar HGZ',
    'chars':[
        u'HGZMF',
        u'HOSPITAL GENERAL DE ZONA',
    ],
},
{
    'tipology_cve': None,
    'tipology': u'HOSPITAL GENERAL DE ZONA',
    'tipologies': None,
    'all_clues': True,
    'prev_clasif_name': u'HGZ',
    'clasif_name': u'Hospital General de Zona',
    'alter_clasifs': u'HGZ HGZMF',
    'chars':[
        u'HGZ ',
        u'HOSPITAL GENERAL DE ZONA',
    ],
},
{
    'tipology_cve': None,
    'tipology': u'HOSPITAL INTEGRAL (COMUNITARIO)',
    'tipologies': None,
    'all_clues': True,
    'prev_clasif_name': u'HIC',
    'clasif_name': u'Hosp Integral Comunitario',
    'alter_clasifs': u'básico hospital',
    'chars':[
        u'H. B. C.',
        u'HOSPITAL BÁSICO COMUNITARIO',
        u'HOSPITAL COMUNITARIO',
        u'HOSPITAL INTEGRAL',
        u'HC',
        u'HI',
    ],
},{
    'tipology_cve': None,
    'tipology': None,
    'tipologies': 'urbano de ',
    'all_clues': False,
    'prev_clasif_name': u'CS Urbano',
    'clasif_name': u'Centro de Salud Urbano',
    'alter_clasifs': u'consulta externa clínica',
    'chars':[
        u'CS Urbano',
        u'Centro de Salud Urbano',
        u'URBANO DE',
        u'URB.DE',
        u'U 0',
        u'U-0',
        u'CSU',
        u'C.S.',
        u'C. S.',
        u'C.S',
        u'CENTRO DE SALUD',
        u'CS',
        u'CENTRO SALUD',
        u'CLÍNICA DE CONSULTA EXTERNA',
    ],
},
{
    'tipology_cve': None,
    'tipology': None,
    'tipologies': 'rural de ',
    'all_clues': False,
    'prev_clasif_name': u'CS Rural',
    'clasif_name': u'Centro de Salud Rural',
    'alter_clasifs': u'consulta externa clínica unidad médica módulo',
    'chars':[
        u'CS Rural',
        u'Centro de Salud Rural',
        u'Unidad Médica tradicional ',
        u'MÓDULO DE MEDICINA TRADICIONAL',
        u'UNIDAD MEDICA RURAL',
        u'UNIDAD MÉDICA RURAL',
        u'RURAL DE ',
        u'U.M.R. ',
        u'R 0',
        u'R-0',
        u'R0',
        u'RUR.DE ',
        u'RUR. DE ',
        u'C.S.',
        u'C. S.',
        u'C.S',
        u'CENTRO DE SALUD',
        u'CS',
        u'CENTRO SALUD',
        u'CLÍNICA DE CONSULTA EXTERNA',
    ],
},{
    'tipology_cve': None,
    'tipology': u'HOSPITAL ESPECIALIZADO',
    'tipologies': None,
    'all_clues': False,
    'prev_clasif_name': u'HG',
    'clasif_name': u'Hospital General',
    'alter_clasifs': u'',
    'chars':[
        u'HOSPITAL GENERAL',
    ],
},
{
    'tipology_cve': None,
    'tipology': u'HOSPITAL GENERAL',
    'tipologies': None,
    'all_clues': False,
    'prev_clasif_name': u'HR',
    'clasif_name': u'Hospital Regional',
    'alter_clasifs': u'general',
    'chars':[
        u'HOSPITAL REGIONAL',
    ],
},
{
    'tipology_cve': '99',
    'tipology': None,
    'tipologies': None,
    'all_clues': False,
    'prev_clasif_name': u'HR',
    'clasif_name': u'Hospital Regional',
    'alter_clasifs': u'general',
    'chars':[
        u'HOSPITAL REGIONAL',
    ],
},
{
    'tipology_cve': None,
    'tipology': u'HOSPITAL GENERAL',
    'tipologies': None,
    'all_clues': True,
    'prev_clasif_name': u'HG',
    'clasif_name': u'Hospital General',
    'alter_clasifs': u'',
    'chars':[
        u'HOSPITAL GENERAL',
        u'HOSPITAL GRAL.',
        u'H.G.',
        u'HG',
    ],
},
]


tipologies2 = [
{
    'tipology_cve': '99',
    'tipology': None,
    'tipologies': None,
    'institution': 'SEDENA',
    'all_clues': False,
    'prev_clasif_name': u'HMR',
    'clasif_name': u'Hospital Militar General',
    'alter_clasifs': None,
    'chars':[
        u'HOSPITAL MILITAR REGIONAL',
    ],
},
{
    #CAMBIO
    'tipology_cve': '99',
    'tipology': None,
    'tipologies': None,
    'institution': 'SEDENA',
    'all_clues': False,
    'prev_clasif_name': u'HMR',
    'clasif_name': u'Hospital Militar de Zona',
    'alter_clasifs': None,
    'chars':[
        u'HOSPITAL MILITAR REGIONAL',
    ],
},
{
    'tipology_cve': '99',
    'tipology': None,
    'tipologies': None,
    'institution': 'SEDENA',
    'all_clues': True,
    'prev_clasif_name': u'SEDENA',
    'clasif_name': u'Secretaría de la Defensa',
    'alter_clasifs': None,
    'chars':[
    ],
},
]

tipologies3 = [
{
    'tipology_cve': 'HR/HAE',
    'tipology': None,
    'tipologies': None,
    'institution': 'ISSSTE',
    'all_clues': False,
    'prev_clasif_name': u'HR/HAE',
    'clasif_name': u'Hosp Reg / Alta Especialidad',
    'alter_clasifs': None,
    'chars':[
    ],
},
{
    #checar NUTRICIÓN
    'tipology_cve': '99',
    'tipology': None,
    'tipologies': None,
    'institution': 'SSA',
    'all_clues': False,
    'prev_clasif_name': u'Inst Nal',
    'clasif_name': u'Instituto Nacional',
    'alter_clasifs': None,
    'chars':[
        u'INSTITUTO NACIONAL DE ',
    ],
},
]

tipologies_f=[{
    'tipology_cve': None,
    'tipology': None,
    'tipologies': None,
    'institution': None,
    'all_clues': True,
    'prev_clasif_name': None,
    'clasif_name': None,
    'alter_clasifs': None,
    'chars':[
    ],
},
]


tipologies_rurb=[{
    'tipology_cve': None,
    'tipology': u'HOSPITAL INTEGRAL (COMUNITARIO)',
    'tipologies': None,
    'all_clues': True,
    'institution': None,
    'prev_clasif_name': u'HIC',
    'clasif_name': u'Hosp Integral Comunitario',
    'alter_clasifs': u'básico hospital',
    'chars':[
        u'H. B. C.',
        u'HOSPITAL BÁSICO COMUNITARIO',
        u'HOSPITAL COMUNITARIO',
        u'HOSPITAL INTEGRAL',
        u'HC',
        u'HI',
    ],
},{
    #no está repetido???
    'tipology_cve': None,
    'tipology': None,
    'tipologies': 'urbano de ',
    'all_clues': True,
    'institution': None,
    'prev_clasif_name': u'CS Urbano',
    'clasif_name': u'Centro de Salud Urbano',
    'alter_clasifs': u'consulta externa clínica',
    'chars':[
        u'CS Urbano',
        u'Centro de Salud Urbano',
        u'URBANO DE',
        u'URB.DE',
        u'U 0',
        u'U-0',
        u'CSU',
        u'C.S.',
        u'C. S.',
        u'C.S',
        u'CENTRO DE SALUD',
        u'CS',
        u'CENTRO SALUD',
        u'CLÍNICA DE CONSULTA EXTERNA',
    ],
},]



def insert_names(clues, tipo, char=False):
    the_clues = clues#.filter(real_name__isnull=True)
    if char:
        the_clues = the_clues.filter(name__istartswith=char)
    len_char = len(char) if char else 0
    the_clues.update(
        alter_clasifs=tipo["alter_clasifs"], 
        clasif_name=tipo["clasif_name"], 
        prev_clasif_name=tipo["prev_clasif_name"])
    for hosp in the_clues:
        real_name = hosp.name[len_char:]
        real_name = " ".join(real_name.split())
        arr_nums = re.findall('\d+', real_name)
        if tipo['tipologies']:
            len_char2 = re.search(r"\d", real_name[:5])
            if len_char2 is not None:
                real_name = hosp.name[len_char2.end():]
                real_name = " ".join(real_name.split())
        elif len(arr_nums):
            hosp.number_unity = arr_nums[0]
        if (len(real_name)) < 4 :
            hosp.real_name = "%s %s"%(real_name, hosp.municipality)
        else:
            hosp.real_name = real_name
        hosp.save()

def rururb():
    for tipo in tipologies_rurb:
        print(tipo["tipology"])
        if tipo["tipology_cve"]:
            clues = CLUES.objects.filter(tipology_cve=tipo["tipology_cve"])
        elif tipo["tipology"]:
            clues = CLUES.objects.filter(tipology=tipo["tipology"])
        elif tipo["tipologies"]:
            clues = CLUES.objects.filter(tipology__istartswith=tipo["tipologies"],)
        else:
            clues = CLUES.objects.filter(real_name__isnull=True, is_searchable=True)
        if tipo["institution"]:
            clues = clues.filter(institution__code=tipo['institution'])
        for char in tipo["chars"]:
            insert_names(clues, tipo, char)
        if (tipo["all_clues"]):
            print(tipo)
            insert_names(clues, tipo)



def insert_names_other():
    clues = CLUES.objects.filter(is_searchable=True,
        prev_clasif_name__isnull=True)
    for hosp in clues:
        len_char= 0
        if (hosp.name.startswith(hosp.tipology_cve)):
            len_char = len(hosp.tipology_cve)
        real_name = hosp.name[len_char:]
        real_name = " ".join(real_name.split())
        arr_nums = re.findall('\d+', real_name)
        if len(arr_nums):
            hosp.number_unity = arr_nums[0]
        if (len(real_name)) < 4:
            hosp.real_name = "%s %s"%(real_name, hosp.municipality)
        else:
            hosp.real_name = real_name
        hosp.clasif_name=hosp.tipology.title()
        hosp.prev_clasif_name=hosp.tipology_cve
        hosp.save()

#insert_names_other()


#Limpieza General:

def general_clean():
    the_clues2 = CLUES.objects.filter(real_name__isnull=False)\
        .exclude(prev_clasif_name='UMF')
    the_clues2.update(
        alter_clasifs=None, 
        clasif_name=None, 
        number_unity=None, 
        prev_clasif_name=None, 
        real_name=None)



#Obtener los números:
def get_numbers():
    for_edit = CLUES.objects.filter(Q(name__icontains="0")|Q(name__icontains="1")
        |Q(name__icontains="2")|Q(name__icontains="3")|Q(name__icontains="4")
        |Q(name__icontains="5")|Q(name__icontains="6")|Q(name__icontains="7")
        |Q(name__icontains="8")|Q(name__icontains="9"))


def unknown_special():
    specials = [{'id':25, 'alter_clasifs': 'juarez'},
    {'id':36, 'alter_clasifs': 'INH'},
    {'id':42, 'alter_clasifs': 'hospital infantil'},
    {'id':31, 'alter_clasifs': 'INP'},
    {'id':15, 'alter_clasifs': 'VEINTE DE NOVIEMBRE 20 DE NOV'},
    {'id':67, 'alter_clasifs': 'NUTRICIÓN, NUTRICION'},
    {'id':34, 'alter_clasifs': 'cancer'},
    {'id':48, 'alter_clasifs': 'cardiología'},
    {'id':70, 'alter_clasifs': 'indre'},
    {'id':20, 'alter_clasifs': 'siglo 21, siglo veintiuno'}]
    for special in specials:
        sp = CLUES.objects.filter(id=special['id'])\
            .update(alter_clasifs=special["alter_clasifs"])
    all_clues = CLUES.objects.filter(is_searchable=True, real_name__isnull=True)\
        .order_by('-total_unities')
    for clue in all_clues[:50]:
        print(clue.name)
        print(clue.institution.public_name)
    all_clues = CLUES.objects.filter(is_searchable=True, state__short_name='Tlaxcala',
        institution__code='ISSSTE').order_by('-total_unities')
    all_clues.count()
    for clue in all_clues[:50]:
        print("--------------------")
        print(clue.name)
        print(clue.real_name)
        print(clue.tipology)
        print(clue.clasif_name)
        print(clue.institution.public_name)



""" ------------------FUTURO----------------- """


HOSPITAL CIVIL DE GUADALAJARA {{NAME}}// {{VARIOS}}

B. HOSPITAL GENERAL CON ESPECIALIDADES JUAN MARÍA DE SALVATIERRA //HOSPITAL GENERAL

CLÍNICA DE ESPECIALIDADES NO. {{N}} // CLÍNICA DE ESPECIALIDADES

DIF MUNICIPAL {{NAME}} /NE

$$ COL. --> COLONIA?

C.A.I.S. {{NAME}} // NE
C.M.D. {{NAME}} // NE
CEDECO {{NAME}} // NE


C.C.S. MENTAL {{NAME}} // CENTRO COMUNITARIO DE SALUD MENTAL


CAIRRS {{NAME}} // CLÍNICA DE ESPECIALIDADES
CE {{NAME}} // CLÍNICA DE ESPECIALIDADES
CENTRO COMUNITARIO DE SALUD MENTAL // CLÍNICA DE ESPECIALIDADES


CENTRO DE ATENCIÓN PRIMARIA PARA LAS ADICCIONES {{VACÍO}} // UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
CAPA {{NAME}} / UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
CENTRO DE ATENCIÓN PRIMARÍA EN ADICCIONES (CAPA {{NAME}})  // UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
CENTRO DE ATENCION PRIMARIA EN ADICCIONES NUEVA VIDA {{NAME}}
CENTRO DE ATENCIÓN PRIMARIA EN ADICCIONES {{NAME}}
CENTRO DE ATENCIÓN PRIMARIA EN ADICCIONES CENTRO NUEVA VIDA {{NAME}}
CENTRO DE ATENCIÓN PRIMARÍA PARA LAS ADICCIONES {{VACÍO}}
UNEME {{NAME}}
UNEME CAPA {{NAME}}
UNEME (CAPA) {{NAME}}
UNEME CAPACIT {{NAME}}
UNEME CISAME {{NAME}}
UNEME CAPACITS {{NAME}}
UNEME-CAPACITS {{NAME}}
UNEME DEDICAM {{NAME}}
UNEMEDECAPA {{NAME}}
UNEME CRÓNICAS {{NAME}}
UNEME CENTRO NUEVA VIDA {{VACÍO}}
UNEME NUEVA VIDA {{VACÍO}}

UNEME DE ENFERMEDADES CRÓNICAS
UNEME ENFERMEDADES CRÓNICAS
UNEME-ENFERMEDADES CRÓNICAS
UNEME DE ENFERMEDADES CRÓNICO-DEGENERATIVAS
UNEME E.C. {{NAME}}
UNEME EC {{NAME}}

CENTRO DE ATENCIÓN PRIMARÍA DE ADICCIONES Y SALUD MENTAL {{VACÍO}}

CENTRO AMBULATORIO DE PREVENCIÓN Y ATENCIÓN DEL SIDA E INFECCIONES DE TRANSMISIÓN SEXUAL (CAPASITS TEPIC) // UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
CENTRO AMBULATORIO PARA LA PREVENCIÓN Y ATENCIÓN DEL SIDA E INFECCIONES DE TRANSMISION SEXUAL CAPASITS ACAPULCO //UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)



CENTRO DE INTEGRACION JUVENIL A.C. {{NAME}} // CLÍNICA DE ESPECIALIDADES
CENTRS DE INTEGRACION JUVENIL A.C. {{NAME}} // CLÍNICA DE ESPECIALIDADES
CENTRO DE INTEGRACION JUVENIL {{NAME}} // CLÍNICA DE ESPECIALIDADES
CENTRO DE INTEGRACIÓN JUVENIL A.C. UNIDAD OPERATIVA {{NAME}}
CENTRO DE INTEGRACIÓN JUVENIL, A.C. UNIDAD OPERATIVA {{NAME}}
CENTROS DE INTEGRACIÓN JUVENIL, A.C. UNIDAD OPERATIVA {{NAME}}

CENTRO DE REHABILITACION INTEGRAL {{NAME}} // NE
CENTRO DE REHABILITACION Y EDUCACION ESPECIAL {{NAME}}//NE

CAPASITS {{NAME}}// UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
CAPASITS {{VACÍO}}// UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES) # INDICAR CON MUNICIPIO


//UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
CENTRO DE SALUD MENTAL



CENTRO REGIONAL DE DESARROLLO INFANTIL {{VACÍO}} //UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
CENTRO REGIONAL DE DESARROLLO INFANTIL Y ESTIMULACION TEMPRANA {{VACÍO}} //UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
CENTRO REGIONAL DE DESARROLLO INFANTIL {{NAME}} //UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)


CENTRO SYGUE {{NAME}}// UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)


CENTRO INTEGRAL DE SALUD MENTAL {{VACÍO}}// UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
CENTRO INTEGRAL DE SALUD MENTAL {{NAME}}// UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)

CENTRO NUEVA VIDA // UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)

CISAME {{NAME}} //UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)



""" ------------------LISTO:----------------- """

UMF {{NOMBRE}} //UNIDAD DE MEDICINA FAMILIAR
UNIDAD DE MEDICINA FAMILIAR {{NOMBRE}} // UNIDAD DE MEDICINA FAMILIAR


CASA DE SALUD // CASA DE SALUD




def unknown_clean():
    import re
    s1 = "thishasadigit4here"
    m = re.search(r"\d", s1).end()
    print(m)
    if m is not None:
        print("Digit found at position", m.start())
        print("Digit found at position", m.end())
    else:
        print("No digit in that string")

    Digit found at position 13


