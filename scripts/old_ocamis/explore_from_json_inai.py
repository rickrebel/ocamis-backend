"""
https://descarga.plataformadetransparencia.org.mx/buscador-ws/descargaArchivo/SISAI/IDXEJ6FXVHNDJYIX5YOGCPPNTLOXGNBYCYYQYGO575EI3XQPOQKGOTTJ2UP637RZDJT4PIP4UV4KA24CVA4Y26AWOMJLSLCX6FTFKBOLEWL7NOE4OWJC3DTGYGTZY7W2?__cf_chl_tk=IxTmTapwNzDlLXNJS3wcocX8zOkf_F.06CQxWKsVjUM-1659329707-0-gaNycGzNCT0

https://serviciospnt.inai.org.mx/inai3/rest/organoGarante/administracionControlDescarga/descargarAdjuntosPorSolicitud/

https://descarga.plataformadetransparencia.org.mx/buscador-ws/descargaArchivo/SISAI/
"""

inai_fiels = [
    {
        "inai_open_search": "idSujetoObligado",
        "model_name": "Entity",
        "final_field": "idSujetoObligado",
    },
    {
        "inai_open_search": "nombreSujetoObligado",
        "model_name": "Entity",
        "final_field": "nombreSujetoObligado",
        "insert": True,
    },
    {
        "inai_open_search": "descripcionSolicitud",
        "model_name": "Petition",
        "final_field": "description_petition",
        "transform": "unescape",
    },
    {
        "inai_open_search": "dsFolio",
        "model_name": "Petition",
        "final_field": "folio_petition",
    },
    {
        "inai_open_search": "fechaEnvio",
        "model_name": "Petition",
        "final_field": "date_send",
        "transform": "date_mex",
    },
    {
        "inai_open_search": "descripcionRespuesta",
        "model_name": "Petition",
        "final_field": "description_response",
        "transform": "unescape",
    },
    {
        "inai_open_search": "dtFechaUltimaRespuesta",
        "model_name": "Petition",
        "final_field": "send_response",
        "transform": "date_mex",
    },
    {
        "inai_open_search": "archivoAdjuntoRespuesta",
        "model_name": "ReplyFile",
        "final_field": "url_download",
        "transform": "join_url",
    },
    {
        "inai_open_search": "id",
        "model_name": "Petition",
        "final_field": "id_inai_open_data",
    },
    {
        "inai_open_search": "informacionQueja",
        "model_name": "Petition",
        "final_field": "info_queja_inai",
        "transform": "to_json",
    },
    {
        "inai_open_search": "datosAdicionales",
        "model_name": "Petition",
        "final_field": "description_petition",
        "transform": "join_lines",
    },

]

examples = {
   "nombreSujetoObligado":"INSTITUTO DE SERVICIOS DE SALUD",
   "nombreOrganoGarante":"BAJA CALIFORNIA SUR",
   "idOrganoGarante":3,
   "idSujetoObligado":735,
   ### Siempre es igual #####
   "tipoSolicitud":"Información pública",
   ### Siempre es igual #####
   "medioEntrada":"Electrónica",
   ### Se puede guardar en text o en nuevo campo - Requiere html.unescape() #####
   "descripcionSolicitud":"1) Se le solicita atentamente que nos proporcione la base de datos, registros de salida de sistema de informaci&oacute;n o mecanismo de control que utilice, asociado a todas las recetas emitidas por los Servicios Estatales de Salud en la entidad en el en el mes de abril y mayo de 2022 y que contemple, cuando menos, las siguientes variables:<br/><br/>Jurisdiccion sanitaria o distrito de salud<br/>Unidad M&eacute;dica (CLUES)<br/>Nivel de atenci&oacute;n<br/>Tipo de unidad m&eacute;dica<br/>Tipo de documento<br/>Folio de documento<br/>Fecha de consulta<br/>Motivo de consulta<br/>Fecha de emisi&oacute;n<br/>Fecha de entrega en farmacia<br/>Clave de medicamento<br/>Descripci&oacute;n de medicamento<br/>Cantidad prescrita<br/>Cantidad entregada<br/>Clave del m&eacute;dico<br/>Nombre del m&eacute;dico<br/>Especialidad del m&eacute;dico<br/><br/>2) Se le solicita atentamente que nos proporcione la base de datos, registros de salida de sistema de informaci&oacute;n o mecanismo de control que utilice, asociado a todas las recetas surtidas totalmente por los Servicios Estatales de Salud en la entidad en el en el mes de abril y mayo de 2022.<br/><br/>3) Se le solicita atentamente que nos proporcione la base de datos, registros de salida de sistema de informaci&oacute;n o mecanismo de control que utilice, asociado a todas las recetas surtidas parcialmente por los Servicios Estatales de Salud en la entidad en el en el mes de abril y mayo de 2022.<br/><br/>4) Se le solicita atentamente que nos proporcione la base de datos, registros de salida de sistema de informaci&oacute;n o mecanismo de control que utilice, asociado a todas las recetas que no fueron surtidas por los Servicios Estatales de Salud en la entidad en el en el mes de abril y mayo de 2022.<br/><br/>5) Se le solicita atentamente que nos proporcione la base de datos, registros de salida de sistema de informaci&oacute;n o mecanismo de control que utilice, asociado a las existencias e inexistencias de medicamentos e insumos en los Servicios Estatales de Salud de la entidad en el en el mes de abril y mayo de 2022.",
   ### folio_petition #####
   "dsFolio":"030073522000163",
   "anioSolicitud":"2022",
   ### dete_send #####
   "fechaEnvio":"08/06/2022",
   ### ¿Se necesita? #####
   "fechaRecepcion":"08/06/2022",
   ### FALTA EL CAMPO #####
   "descripcionRespuesta":"Se adjunta respuesta",
   ### ANALIZAR RESPUESTAS (EXCEL) #####
   "modalidadEntrega":"Electrónico a través del sistema de solicitudes de acceso a la información de la PNT",
   ### ¿Se necesita? #####
   "dtFechaUltimaRespuesta":"16/06/2022",
   ### ANALIZAR RESPUESTAS (EXCEL) #####
   "tipoRespuesta":"Notificación de respuesta de información disponible vía PNT",
   ### FALTA EL CAMPO #####
   "archivoAdjuntoRespuesta":[
      "IDXEJ6FXVHNDJYIX5YOGCPPNTLOXGNBYCYYQYGO575EI3XQPOQKGOTTJ2UP637RZDJT4PIP4UV4KA24CVA4Y26AWOMJLSLCX6FTFKBOLEWL7NOE4OWJC3DTGYGTZY7W2"
   ],
   ### En ningún caso existe #####
   "archivoAdjuntoSolicitante":[
      "SIN_ARCHIVO"
   ],
   ### FALTA EL CAMPO #####
   "id":6724947,
   "archivoAdjuntoRespuestaNombre":[
      "030073522000163 RESP.pdf"
   ],
   ### ANALIZAR DESPLIEGUE #####
   "informacionQueja":"{\"RECURSO_ACUMULADOR\":\"\",\"SENTIDO_RESOLUCION\":\"Modifica\",\"FECHA_CUMPLIMIENTO\":\"\",\"FECHA_OFICIAL\":\"28/04/2022\",\"AMPLIADO\":\"Sí\",\"LIMITE_VOTAR\":\"\",\"SIGLAS_COMISIONADO\":\"Adrián Alcalá Méndez\",\"ACUERDO_CUMPLIMIENTO\":\"\",\"TIPO_MEDIO_IMPUGNACION\":2,\"RESPUESTA_SOLICITUD\":\"\",\"ID_MEDIO_IMPUGNACION\":210864,\"FECHA_RESOLUCION\":\"01/06/2022\",\"ARCHIVO\":\"\",\"FECHA_ADMISION\":\"06/05/2022\",\"MEDIO_ADMISION\":\"\",\"ACTO_RECURRIDO\":\"Le solicito de la manera mas atenta completar la información solicitada en los siguientes puntos: \\n\\n1. Hace falta el registro de medicamentos y/o recetas no surtidas en su totalidad y las no surtidas en lo absoluto. \\n2. Algún registro que compare lo solicitado con lo surtido. \\n\\nSin la intención de que se realicen documentos a doc, o que se procese la información. Con lo que se cuente en el formato que se tenga. \\n\\nGracias\",\"NOTIFICACION_RESOLUCION\":\"\",\"RECURSOS_ACUMULADOS\":\"\",\"NOMBRE_PROMOVENTE\":\"\",\"FECHA_NOTIFICACION_ADM\":\"\",\"ID_ORGANO_GARANTE\":33,\"EXPEDIENTE\":\"RRA 6220/22\",\"SUJETO_OBLIGADO\":\"Instituto Nacional de Enfermedades Respiratorias Ismael Cosío Villegas (INER)\",\"FECHA_CIERRE\":\"\",\"FECHA_ADMISION_SO\":\"10/05/2022\",\"ID_SUJETO_OBLIGADO\":192,\"FOLIO_SOLICITUD\":\"330019222000213\",\"FECHA_PREVENCION\":\"\",\"MEDIO_NOTIFICACION\":\"\",\"FECHA_AMPLIACION\":\"\",\"FECHA_RESPUESTA_PREV\":\"\"}",
   ### FALTA EL CAMPO #####
   "datosAdicionales":"Sabemos que la información solicitada es muy pesada por lo que le solicitamos amablemente indicarnos el lugar, fecha, hora y el nombre de un contacto para acudir de manera presencial con un dispositivo de memoria para cargar la información solicitada."
}


eplore_compain = {'ACTO_RECURRIDO': 'Le solicito de la manera mas atenta completar la '
                   'información solicitada en los siguientes puntos: \n'
                   '\n'
                   '1. Hace falta el registro de medicamentos y/o recetas no '
                   'surtidas en su totalidad y las no surtidas en lo '
                   'absoluto. \n'
                   '2. Algún registro que compare lo solicitado con lo '
                   'surtido. \n'
                   '\n'
                   'Sin la intención de que se realicen documentos a doc, o '
                   'que se procese la información. Con lo que se cuente en el '
                   'formato que se tenga. \n'
                   '\n'
                   'Gracias',
 'ACUERDO_CUMPLIMIENTO': '',
 'AMPLIADO': 'Sí',
 'ARCHIVO': '',
 'EXPEDIENTE': 'RRA 6220/22',
 'FECHA_ADMISION': '06/05/2022',
 'FECHA_ADMISION_SO': '10/05/2022',
 'FECHA_AMPLIACION': '',
 'FECHA_CIERRE': '',
 'FECHA_CUMPLIMIENTO': '',
 'FECHA_NOTIFICACION_ADM': '',
 'FECHA_OFICIAL': '28/04/2022',
 'FECHA_PREVENCION': '',
 'FECHA_RESOLUCION': '01/06/2022',
 'FECHA_RESPUESTA_PREV': '',
 'FOLIO_SOLICITUD': '330019222000213',
 'ID_MEDIO_IMPUGNACION': 210864,
 'ID_ORGANO_GARANTE': 33,
 'ID_SUJETO_OBLIGADO': 192,
 'LIMITE_VOTAR': '',
 'MEDIO_ADMISION': '',
 'MEDIO_NOTIFICACION': '',
 'NOMBRE_PROMOVENTE': '',
 'NOTIFICACION_RESOLUCION': '',
 'RECURSOS_ACUMULADOS': '',
 'RECURSO_ACUMULADOR': '',
 'RESPUESTA_SOLICITUD': '',
 'SENTIDO_RESOLUCION': 'Modifica',
 'SIGLAS_COMISIONADO': 'Adrián Alcalá Méndez',
 'SUJETO_OBLIGADO': 'Instituto Nacional de Enfermedades Respiratorias Ismael '
                    'Cosío Villegas (INER)',
 'TIPO_MEDIO_IMPUGNACION': 2}



import io
import json
from pprint import pprint
data = None
path_json = "C:\\Users\\Ricardo\\Desktop\\experimentos\\todas.json"

with io.open(path_json, "r", encoding="UTF-8") as file:
    data = json.load(file)
    file.close()

#data["solicitudes"][0].keys()



all_complains = []
for pet in data["solicitudes"]:
    try:
        queja = pet["informacionQueja"]
    except Exception as e:
        print(e)
        continue
    queja = json.loads(queja)
    all_complains.append(queja)

#print(all_complains)



def get_columns(collection):
    all_keys = {}
    for pet in collection:
        current_keys = pet.keys()
        for my_key in current_keys:
            if my_key not in all_keys:
                all_keys[my_key] = pet[my_key]
    return all_keys

def print_columns():
    print(get_columns(data["solicitudes"]))
    print("\n ----------- \n")
    pprint(get_columns(data["solicitudes"]))


def print_complains():
    print(get_columns(all_complains))
    print("\n ----------- \n")
    pprint(get_columns(all_complains))


def get_values(collection, my_key):
    all_values = []
    for elem in collection:
        try:
            value = elem[my_key]
        except Exception as e:
            print(e)
            continue
        if value not in all_values:
            all_values.append(value)
    return all_values

get_values(data["solicitudes"], "descripcionRespuesta")
all_values = 2
print(all_values)
pprint(all_values)


def get_many_values(collection, keys):
    final_values = {}
    for elem in collection:
        current_values = {}
        for key in keys:
            try:
                value = elem[key]
                current_values[key] = value
            except Exception as e:
                print(e)
                continue
        list_values = [str(val) for val in current_values.values()]
        string_key = "|".join(list_values)
        if string_key not in final_values:
            final_values[string_key] = current_values
    return final_values

related_keys = [
    "nombreSujetoObligado", "nombreOrganoGarante", "idOrganoGarante",
    "idSujetoObligado"]
all_dict_values = get_many_values(data["solicitudes"], related_keys)
list(all_dict_values.values())



import html
s = "&amp;"
decoded = html.unescape(s)
# &
