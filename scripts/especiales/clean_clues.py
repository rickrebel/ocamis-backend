import re
from django.db.models import Q
from catalog.models import State, Institution, CLUES

# ------------EJEMPLO HIDRATED---------------- #


def import_clues():
    import csv
    from pprint import pprint
    from django.utils.dateparse import parse_datetime
    with open('clues.csv') as csv_file:
        #contents = f.read().decode("UTF-8")
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
                clues = CLUES.objects.create()
                print(clues)


def set_searchable_clues():
    from django.db.models import Q
    is_search = CLUES.objects.filter(status_operation='EN OPERACION')\
        .exclude(Q(institution__code='SMP')|Q(institution__code='HUN')
            |Q(institution__code='CIJ')|Q(institution__code='CRO')
            |Q(establishment_type='DE APOYO')
            |Q(establishment_type='DE ASISTENCIA SOCIAL')
            |Q(typology_cve='BS')|Q(typology_cve='X')
            |Q(typology_cve='P')|Q(typology_cve='UMM'))
    print("count: %s" % is_search.count())
    is_search.update(is_searchable=True)


def update_institution_public():
    for institution in Institution.objects.all():
        institution.public_name = institution.name
        institution.public_code = institution.code
        institution.save()


typologies = [
    {
        'typology_cve': 'UMF',
        'typology': None,
        'typologies': None,
        'all_clues': True,
        'prev_clasif_name': 'UMF',
        'clasif_name': 'Unidad Médica Familiar',
        'alter_clasifs': 'unidad de medicina familiar',
        'chars':['UMF ', 'Unidad de Medicina Familiar No. '
            ,'Unidad de Medicina Familiar No.','Unidad de Medicina Familiar ',
            'UMF No','U.H.F. ','UMF/UMAA '],
    },{
        'typology_cve': None,
        'typology': 'CASA DE SALUD',
        'typologies': None,
        'all_clues': True,
        'prev_clasif_name': 'Casa de S.',
        'clasif_name': 'Casa de Salud',
        'alter_clasifs': '',
        'chars':['Casa de salud '],
    },{
        'typology_cve': None,
        'typology': 'CLÍNICA DE ESPECIALIDADES',
        'typologies': None,
        'all_clues': False,
        'prev_clasif_name': 'Clínica de Esp.',
        'clasif_name': 'Clínica de Especialidades',
        'alter_clasifs': None,
        'chars':['CE '],
    },{
        'typology_cve': '99',
        'typology': None,
        'typologies': None,
        'all_clues': False,
        'prev_clasif_name': 'CRI',
        'clasif_name': 'Centro de Rehabilitación Integral',
        'alter_clasifs': 'educación especial',
        'chars':[
            'CENTRO DE REHABILITACION INTEGRAL (CRI)',
            'CENTRO DE REHABILITACION INTEGRAL ',
            'CENTRO DE REHABILITACION Y EDUCACION ESPECIAL '],
    },{
        'typology_cve': 'CAAPS',
        'typology': None,
        'typologies': None,
        'all_clues': True,
        'prev_clasif_name': 'CAAPS',
        'clasif_name': 'Centro de Rehabilitación Integral',
        'alter_clasifs': 'ceaps ceap cap cedral caap',
        'chars':['CAAPS ','CEAPS ','CENTRO DE SALUD CEDRAL','CENTRO DE SALUD ',
            'CENTRO AVANZADO DE ATENCIÓN PRIMARIA A LA  SALUD',
            'CENTRO AVANZADO DE ATENCIÓN PRIMARÍA A LA SALUD',
            'CENTRO ESPECIALIZADO EN ATENCIÓN PRIMARIA A LA SALUD'],
    },{
        'typology_cve': None,
        'typology': 'CENTRO DE SALUD CON HOSPITALIZACIÓN',
        'typologies': None,
        'all_clues': True,
        'prev_clasif_name': 'CS c/Hosp',
        'clasif_name': 'C. de Salud con Hospitalización',
        'alter_clasifs': 'clínica regional',
        'chars':[
            'CENTRO DE SALUD CON HOSPITALIZACIÓN',
            'CENTRO DE SALUD CON HOSPITAL',
            'C.S. C/ HOSPITALIZACIÓN'
            'CSC/H '
            'CLINICA REGIONAL'
        ],
    },{
        'typology_cve': None,
        'typology': 'CENTROS DE SALUD CON SERVICIOS AMPLIADOS',
        'typologies': None,
        'all_clues': True,
        'prev_clasif_name': 'CESSA',
        'clasif_name': 'C. de Salud con Serv. Ampliados',
        'alter_clasifs': 'cesa',
        'chars':[
            'CENTRO DE SALUD DE SERVICIOS AMPLIADOS DE',
            'CENTRO DE SALUD CON SERVICIOS AMPLIADOS (CESSA)',
            'CENTRO DE SALUD CON SERVICIOS AMPLIADOS',
            'CENTRO DE SALUD',
            'CESSA',
            'CESA'
        ],
    },
    {
        'typology_cve': None,
        'typology': 'HOSPITAL ESPECIALIZADO',
        'typologies': None,
        'all_clues': False,
        'prev_clasif_name': 'H Esp',
        'clasif_name': 'Hospital Especializado',
        'alter_clasifs': 'especialidades',
        'chars':[
            'HIES',
        ],
    },{
        'typology_cve': None,
        'typology': 'HOSPITAL ESPECIALIZADO',
        'typologies': None,
        'all_clues': False,
        'prev_clasif_name': 'H Ped',
        'clasif_name': 'Hospital Pediátrico',
        'alter_clasifs': 'pediatría',
        'chars':[
            'HOSPITAL PEDIÁTRICO',
        ],
    },{
        'typology_cve': None,
        'typology': 'HOSPITAL ESPECIALIZADO',
        'typologies': None,
        'all_clues': False,
        'prev_clasif_name': 'H Mat-Inf',
        'clasif_name': 'Hospital Materno Infantil',
        'alter_clasifs': 'pediatría',
        'chars':[
            'HOSPITAL MATERNO INFANTIL',
        ],
    },{
        'typology_cve': None,
        'typology': 'HOSPITAL ESPECIALIZADO',
        'typologies': None,
        'all_clues': False,
        'prev_clasif_name': 'H Mujer',
        'clasif_name': 'Hospital de la Mujer',
        'alter_clasifs': None,
        'chars':[
            'HOSPITAL DE LA MUJER',
        ],
    },{
        'typology_cve': None,
        'typology': 'HOSPITAL ESPECIALIZADO',
        'typologies': None,
        'all_clues': False,
        'prev_clasif_name': 'HRAE Mujer',
        'clasif_name': 'Hosp. Reg. de Alta Espec. de la Mujer',
        'alter_clasifs': 'especialidad hospital regional',
        'chars':[
            'HOSPITAL REGIONAL DE ALTA ESPECIALIDAD DE LA MUJER',
        ],
    },{
        'typology_cve': None,
        'typology': 'HOSPITAL ESPECIALIZADO',
        'typologies': None,
        'all_clues': False,
        'prev_clasif_name': 'HRAE',
        'clasif_name': 'Hosp. Reg. de Alta Especialidad',
        'alter_clasifs': 'hospital regional',
        'chars':[
            'HOSPITAL REGIONAL DE ALTA ESPECIALIDAD',
        ],
    },{
        #CAMBIO
        'typology_cve': None,
        'typology': 'HOSPITAL DE GINECO-PEDIATRÍA',
        'typologies': None,
        'all_clues': True,
        'prev_clasif_name': 'H Esp',
        'clasif_name': 'Hospital de Ginecopediatría',
        'alter_clasifs': 'especialidades',
        'chars':[
            'HGP',
        ],
    },{
        'typology_cve': None,
        'typology': 'HOSPITAL DE GINECO-OBSTETRICIA',
        'typologies': None,
        'all_clues': True,
        'prev_clasif_name': 'HGO',
        'clasif_name': 'Hospital de Gineco Obstetricia',
        'alter_clasifs': 'ginecológico',
        'chars':[
            'HGO',
        ],
    },{
        'typology_cve': None,
        'typology': 'HOSPITAL DE GINECO-OBSTETRICIA CON MEDICINA FAMILIAR',
        'typologies': None,
        'all_clues': True,
        'prev_clasif_name': 'HGOMF',
        'clasif_name': 'H. de Gineco-Obstetricia con Med. Fam.',
        'alter_clasifs': 'ginecologico medicina familiar hospital',
        'chars':[
            'HGOMF',
        ],
    },{
        'typology_cve': None,
        'typology': 'HOSPITAL GENERAL DE SUBZONA',
        'typologies': None,
        'all_clues': True,
        'prev_clasif_name': 'HGSZ',
        'clasif_name': 'Hospital Gral de Subzona',
        'alter_clasifs': 'general subzona',
        'chars':[
            'HGS',
        ],
    },{
        'typology_cve': None,
        'typology': 'HOSPITAL GENERAL DE SUBZONA CON MEDICINA FAMILIAR',
        'typologies': None,
        'all_clues': True,
        'prev_clasif_name': 'HRAE Mujer',
        'clasif_name': 'Hosp Gral de Subzona con Med Fam',
        'alter_clasifs': ' HOSPITAL GENERAL MEDICINA FAMILIAR',
        'chars':[
            'HGSMF',
        ],
    },{
        'typology_cve': None,
        'typology': 'HOSPITAL DE ESPECIALIDADES',
        'typologies': None,
        'all_clues': True,
        'prev_clasif_name': 'HE',
        'clasif_name': 'Hospital de Especialidades',
        'alter_clasifs': None,
        'chars':[
            'HES',
        ],
    },{
        'typology_cve': None,
        'typology': 'HOSPITAL PSIQUIÁTRICO',
        'typologies': None,
        'all_clues': True,
        'prev_clasif_name': 'H Psiq',
        'clasif_name': 'Hospital Psiquiátrico',
        'alter_clasifs': 'psiquiatra',
        'chars':[
            'HOSPITAL PSIQUIÁTRICO',
        ],
    },{
        'typology_cve': None,
        'typology': 'HOSPITAL GENERAL REGIONAL',
        'typologies': None,
        'all_clues': True,
        'prev_clasif_name': 'HGR',
        'clasif_name': 'Hospital General Regional',
        'alter_clasifs': '',
        'chars':[
            'HGR',
            'HOSPITAL GENERAL REGIONAL',
        ],
    },
    {
        'typology_cve': None,
        'typology': 'HOSPITAL GENERAL DE ZONA CON MEDICINA FAMILIAR',
        'typologies': None,
        'all_clues': True,
        'prev_clasif_name': 'HGZMF',
        'clasif_name': 'Hosp Gral de Zona con Med Fam',
        'alter_clasifs': 'Hospital General de Medicina Familiar HGZ',
        'chars':[
            'HGZMF',
            'HOSPITAL GENERAL DE ZONA',
        ],
    },
    {
        'typology_cve': None,
        'typology': 'HOSPITAL GENERAL DE ZONA',
        'typologies': None,
        'all_clues': True,
        'prev_clasif_name': 'HGZ',
        'clasif_name': 'Hospital General de Zona',
        'alter_clasifs': 'HGZ HGZMF',
        'chars':[
            'HGZ ',
            'HOSPITAL GENERAL DE ZONA',
        ],
    },
    {
        'typology_cve': None,
        'typology': 'HOSPITAL INTEGRAL (COMUNITARIO)',
        'typologies': None,
        'all_clues': True,
        'prev_clasif_name': 'HIC',
        'clasif_name': 'Hosp Integral Comunitario',
        'alter_clasifs': 'básico hospital',
        'chars':[
            'H. B. C.',
            'HOSPITAL BÁSICO COMUNITARIO',
            'HOSPITAL COMUNITARIO',
            'HOSPITAL INTEGRAL',
            'HC',
            'HI',
        ],
    },{
        'typology_cve': None,
        'typology': None,
        'typologies': 'urbano de ',
        'all_clues': False,
        'prev_clasif_name': 'CS Urbano',
        'clasif_name': 'Centro de Salud Urbano',
        'alter_clasifs': 'consulta externa clínica',
        'chars':[
            'CS Urbano',
            'Centro de Salud Urbano',
            'URBANO DE',
            'URB.DE',
            'U 0',
            'U-0',
            'CSU',
            'C.S.',
            'C. S.',
            'C.S',
            'CENTRO DE SALUD',
            'CS',
            'CENTRO SALUD',
            'CLÍNICA DE CONSULTA EXTERNA',
        ],
    },
    {
        'typology_cve': None,
        'typology': None,
        'typologies': 'rural de ',
        'all_clues': False,
        'prev_clasif_name': 'CS Rural',
        'clasif_name': 'Centro de Salud Rural',
        'alter_clasifs': 'consulta externa clínica unidad médica módulo',
        'chars':[
            'CS Rural',
            'Centro de Salud Rural',
            'Unidad Médica tradicional ',
            'MÓDULO DE MEDICINA TRADICIONAL',
            'UNIDAD MEDICA RURAL',
            'UNIDAD MÉDICA RURAL',
            'RURAL DE ',
            'U.M.R. ',
            'R 0',
            'R-0',
            'R0',
            'RUR.DE ',
            'RUR. DE ',
            'C.S.',
            'C. S.',
            'C.S',
            'CENTRO DE SALUD',
            'CS',
            'CENTRO SALUD',
            'CLÍNICA DE CONSULTA EXTERNA',
        ],
    },{
        'typology_cve': None,
        'typology': 'HOSPITAL ESPECIALIZADO',
        'typologies': None,
        'all_clues': False,
        'prev_clasif_name': 'HG',
        'clasif_name': 'Hospital General',
        'alter_clasifs': '',
        'chars':[
            'HOSPITAL GENERAL',
        ],
    },
    {
        'typology_cve': None,
        'typology': 'HOSPITAL GENERAL',
        'typologies': None,
        'all_clues': False,
        'prev_clasif_name': 'HR',
        'clasif_name': 'Hospital Regional',
        'alter_clasifs': 'general',
        'chars':[
            'HOSPITAL REGIONAL',
        ],
    },
    {
        'typology_cve': '99',
        'typology': None,
        'typologies': None,
        'all_clues': False,
        'prev_clasif_name': 'HR',
        'clasif_name': 'Hospital Regional',
        'alter_clasifs': 'general',
        'chars':[
            'HOSPITAL REGIONAL',
        ],
    },
    {
        'typology_cve': None,
        'typology': 'HOSPITAL GENERAL',
        'typologies': None,
        'all_clues': True,
        'prev_clasif_name': 'HG',
        'clasif_name': 'Hospital General',
        'alter_clasifs': '',
        'chars':[
            'HOSPITAL GENERAL',
            'HOSPITAL GRAL.',
            'H.G.',
            'HG',
        ],
    },
    ]

typologies2 = [
    {
        'typology_cve': '99',
        'typology': None,
        'typologies': None,
        'institution': 'SEDENA',
        'all_clues': False,
        'prev_clasif_name': 'HMR',
        'clasif_name': 'Hospital Militar General',
        'alter_clasifs': None,
        'chars':[
            'HOSPITAL MILITAR REGIONAL',
        ],
    },
    {
        #CAMBIO
        'typology_cve': '99',
        'typology': None,
        'typologies': None,
        'institution': 'SEDENA',
        'all_clues': False,
        'prev_clasif_name': 'HMR',
        'clasif_name': 'Hospital Militar de Zona',
        'alter_clasifs': None,
        'chars':[
            'HOSPITAL MILITAR REGIONAL',
        ],
    },
    {
        'typology_cve': '99',
        'typology': None,
        'typologies': None,
        'institution': 'SEDENA',
        'all_clues': True,
        'prev_clasif_name': 'SEDENA',
        'clasif_name': 'Secretaría de la Defensa',
        'alter_clasifs': None,
        'chars':[
        ],
    },
    ]

typologies3 = [
    {
        'typology_cve': 'HR/HAE',
        'typology': None,
        'typologies': None,
        'institution': 'ISSSTE',
        'all_clues': False,
        'prev_clasif_name': 'HR/HAE',
        'clasif_name': 'Hosp Reg / Alta Especialidad',
        'alter_clasifs': None,
        'chars':[
        ],
    },
    {
        #checar NUTRICIÓN
        'typology_cve': '99',
        'typology': None,
        'typologies': None,
        'institution': 'SSA',
        'all_clues': False,
        'prev_clasif_name': 'Inst Nal',
        'clasif_name': 'Instituto Nacional',
        'alter_clasifs': None,
        'chars':[
            'INSTITUTO NACIONAL DE ',
        ],
    }]

typologies_f=[{
    'typology_cve': None,
    'typology': None,
    'typologies': None,
    'institution': None,
    'all_clues': True,
    'prev_clasif_name': None,
    'clasif_name': None,
    'alter_clasifs': None,
    'chars':[
    ],
},
]


typologies_rurb=[
    {
        'typology_cve': None,
        'typology': 'HOSPITAL INTEGRAL (COMUNITARIO)',
        'typologies': None,
        'all_clues': True,
        'institution': None,
        'prev_clasif_name': 'HIC',
        'clasif_name': 'Hosp Integral Comunitario',
        'alter_clasifs': 'básico hospital',
        'chars':[
            'H. B. C.',
            'HOSPITAL BÁSICO COMUNITARIO',
            'HOSPITAL COMUNITARIO',
            'HOSPITAL INTEGRAL',
            'HC',
            'HI',
        ],
    },{
        #no está repetido???
        'typology_cve': None,
        'typology': None,
        'typologies': 'urbano de ',
        'all_clues': True,
        'institution': None,
        'prev_clasif_name': 'CS Urbano',
        'clasif_name': 'Centro de Salud Urbano',
        'alter_clasifs': 'consulta externa clínica',
        'chars':[
            'CS Urbano',
            'Centro de Salud Urbano',
            'URBANO DE',
            'URB.DE',
            'U 0',
            'U-0',
            'CSU',
            'C.S.',
            'C. S.',
            'C.S',
            'CENTRO DE SALUD',
            'CS',
            'CENTRO SALUD',
            'CLÍNICA DE CONSULTA EXTERNA',
        ],
    }]


def insert_names(clues, tipo, char=""):
    the_clues = clues  # .filter(real_name__isnull=True)
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
        arr_nums = re.findall(r'\d+', real_name)
        if tipo['typologies']:
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


def rururb(current_list):
    for tipo in current_list:
        print(tipo["typology"])
        clues = CLUES.objects.filter(real_name__isnull=True, is_searchable=True)
        if tipo["typology_cve"]:
            clues.filter(typology_cve=tipo["typology_cve"])
        elif tipo["typology"]:
            clues.filter(typology=tipo["typology"])
        elif tipo["typologies"]:
            clues.filter(typology__istartswith=tipo["typologies"],)
        else:
            clues.filter(real_name__isnull=True, is_searchable=True)
        if "institution" in tipo:
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
        len_char = 0
        if (hosp.name.startswith(hosp.typology_cve)):
            len_char = len(hosp.typology_cve)
        real_name = hosp.name[len_char:]
        real_name = " ".join(real_name.split())
        arr_nums = re.findall('\d+', real_name)
        if len(arr_nums):
            hosp.number_unity = arr_nums[0]
        if (len(real_name)) < 4:
            hosp.real_name = "%s %s"%(real_name, hosp.municipality)
        else:
            hosp.real_name = real_name
        hosp.clasif_name=hosp.typology.title()
        hosp.prev_clasif_name=hosp.typology_cve
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
        print(clue.typology)
        print(clue.clasif_name)
        print(clue.institution.public_name)



""" ------------------FUTURO----------------- """


# HOSPITAL CIVIL DE GUADALAJARA {{NAME}}// {{VARIOS}}
#
# B. HOSPITAL GENERAL CON ESPECIALIDADES JUAN MARÍA DE SALVATIERRA //HOSPITAL GENERAL
#
# CLÍNICA DE ESPECIALIDADES NO. {{N}} // CLÍNICA DE ESPECIALIDADES
#
# DIF MUNICIPAL {{NAME}} /NE
#
# $$ COL. --> COLONIA?
#
# C.A.I.S. {{NAME}} // NE
# C.M.D. {{NAME}} // NE
# CEDECO {{NAME}} // NE
#
#
# C.C.S. MENTAL {{NAME}} // CENTRO COMUNITARIO DE SALUD MENTAL
#
#
# CAIRRS {{NAME}} // CLÍNICA DE ESPECIALIDADES
# CE {{NAME}} // CLÍNICA DE ESPECIALIDADES
# CENTRO COMUNITARIO DE SALUD MENTAL // CLÍNICA DE ESPECIALIDADES
#
#
# CENTRO DE ATENCIÓN PRIMARIA PARA LAS ADICCIONES {{VACÍO}} // UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
# CAPA {{NAME}} / UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
# CENTRO DE ATENCIÓN PRIMARÍA EN ADICCIONES (CAPA {{NAME}})  // UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
# CENTRO DE ATENCION PRIMARIA EN ADICCIONES NUEVA VIDA {{NAME}}
# CENTRO DE ATENCIÓN PRIMARIA EN ADICCIONES {{NAME}}
# CENTRO DE ATENCIÓN PRIMARIA EN ADICCIONES CENTRO NUEVA VIDA {{NAME}}
# CENTRO DE ATENCIÓN PRIMARÍA PARA LAS ADICCIONES {{VACÍO}}
# UNEME {{NAME}}
# UNEME CAPA {{NAME}}
# UNEME (CAPA) {{NAME}}
# UNEME CAPACIT {{NAME}}
# UNEME CISAME {{NAME}}
# UNEME CAPACITS {{NAME}}
# UNEME-CAPACITS {{NAME}}
# UNEME DEDICAM {{NAME}}
# UNEMEDECAPA {{NAME}}
# UNEME CRÓNICAS {{NAME}}
# UNEME CENTRO NUEVA VIDA {{VACÍO}}
# UNEME NUEVA VIDA {{VACÍO}}
#
# UNEME DE ENFERMEDADES CRÓNICAS
# UNEME ENFERMEDADES CRÓNICAS
# UNEME-ENFERMEDADES CRÓNICAS
# UNEME DE ENFERMEDADES CRÓNICO-DEGENERATIVAS
# UNEME E.C. {{NAME}}
# UNEME EC {{NAME}}
#
# CENTRO DE ATENCIÓN PRIMARÍA DE ADICCIONES Y SALUD MENTAL {{VACÍO}}
#
# CENTRO AMBULATORIO DE PREVENCIÓN Y ATENCIÓN DEL SIDA E INFECCIONES DE TRANSMISIÓN SEXUAL (CAPASITS TEPIC) // UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
# CENTRO AMBULATORIO PARA LA PREVENCIÓN Y ATENCIÓN DEL SIDA E INFECCIONES DE TRANSMISION SEXUAL CAPASITS ACAPULCO //UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
#
#
#
# CENTRO DE INTEGRACION JUVENIL A.C. {{NAME}} // CLÍNICA DE ESPECIALIDADES
# CENTRS DE INTEGRACION JUVENIL A.C. {{NAME}} // CLÍNICA DE ESPECIALIDADES
# CENTRO DE INTEGRACION JUVENIL {{NAME}} // CLÍNICA DE ESPECIALIDADES
# CENTRO DE INTEGRACIÓN JUVENIL A.C. UNIDAD OPERATIVA {{NAME}}
# CENTRO DE INTEGRACIÓN JUVENIL, A.C. UNIDAD OPERATIVA {{NAME}}
# CENTROS DE INTEGRACIÓN JUVENIL, A.C. UNIDAD OPERATIVA {{NAME}}
#
# CENTRO DE REHABILITACION INTEGRAL {{NAME}} // NE
# CENTRO DE REHABILITACION Y EDUCACION ESPECIAL {{NAME}}//NE
#
# CAPASITS {{NAME}}// UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
# CAPASITS {{VACÍO}}// UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES) # INDICAR CON MUNICIPIO
#
#
# //UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
# CENTRO DE SALUD MENTAL
#
#
#
# CENTRO REGIONAL DE DESARROLLO INFANTIL {{VACÍO}} //UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
# CENTRO REGIONAL DE DESARROLLO INFANTIL Y ESTIMULACION TEMPRANA {{VACÍO}} //UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
# CENTRO REGIONAL DE DESARROLLO INFANTIL {{NAME}} //UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
#
#
# CENTRO SYGUE {{NAME}}// UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
#
#
# CENTRO INTEGRAL DE SALUD MENTAL {{VACÍO}}// UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
# CENTRO INTEGRAL DE SALUD MENTAL {{NAME}}// UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
#
# CENTRO NUEVA VIDA // UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
#
# CISAME {{NAME}} //UNIDAD DE ESPECIALIDADES MÉDICAS (UNEMES)
#
#
#
# """ ------------------LISTO:----------------- """
#
# UMF {{NOMBRE}} //UNIDAD DE MEDICINA FAMILIAR
# UNIDAD DE MEDICINA FAMILIAR {{NOMBRE}} // UNIDAD DE MEDICINA FAMILIAR
#
#
# CASA DE SALUD // CASA DE SALUD




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

    # Digit found at position 13


