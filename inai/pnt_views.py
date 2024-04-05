

# Ejemplo de respuesta:

example_request = {
    "dtFechaRecepcion": "04/04/2024",
    "idUsuario": 39039491,
    "nombre": "",
    "apellidoPaterno": "",
    "apellidoMaterno": "",
    "nombreRepresentante": "Berenice",
    "apellidoPaternoRepresentante": "Cruz",
    "apellidoMaternoRepresentante": "Maya",
    "nombreRazonSocial": "Observatorio Ciudadano para el Acceso a Medicamentos e Insumos de la Salud",
    "tipoSolicitud": 2,
    "idMedioEntrada": 0,
    "sujetosObligados": [
        {
            "idSujetoObligado": 180,
            "dsSujetoObligado": "Instituto Mexicano del Seguro Social (IMSS)",
            "idOrganoGarante": 33,
            "dsOrganoGarante": "Federación"
        }
    ],
    "ocupaciones": [

    ],
    "accesibilidad": [

    ],
    "idTipoSolicitante": 2,
    "fgEstadisticos": 0,
    "selectOrganoGaranteIP": {
        "idOrganoGarante": 33,
        "dsNombre": "Federación"
    },
    "isDisabledOg": false,
    "isDisabledSo": false,
    "showIconDelete": true,
    "informacionSolicitada": "1) Se le solicita atentamente que nos proporcione (en formatos compatibles con .csv, .txt, .xls o .xlsx) la base de datos, registros de salida de sistema de información o mecanismo de control que utilice, asociado a todas las recetas emitidas por la institución en el mes de MARZO de 2024 y que contemple, cuando menos, las siguientes variables:\n\nJurisdiccion sanitaria o Distrito de Salud\nNombre de Unidad Médica\nClave CLUES de Unidad Médica\nFolio o identificador de receta\nFecha de consulta o emisión\nFecha de entrega en farmacia\nMotivo de consulta\nDiagnóstico\nClave de medicamento\nDescripción de medicamento\nCantidad prescrita\nCantidad entregada\nClave del médico\nNombre del médico\n\n2) Se le solicita atentamente que nos proporcione (en formatos compatibles con .csv, .txt, .xls o .xlsx) la base de datos, registros de salida de sistema de información o mecanismo de control que utilice, asociado a todas las recetas surtidas totalmente,  recetas surtidas parcialmente y todas las recetas que no fueron surtidas por la institución en el mes de MARZO de 2024.\n\n\n3) Se le solicita atentamente que nos proporcione (en formatos compatibles con .csv, .txt, .xls o .xlsx) la base de datos, registros de salida de sistema de información o mecanismo de control que utilice, asociado a las existencias e inexistencias de medicamentos e insumos en la institución en el mes de MARZO de 2024.\n\nSabemos que la información solicitada es muy pesada por lo que le solicitamos amablemente indicarnos el lugar, fecha, hora y el nombre de un contacto para acudir de manera presencial con un dispositivo de memoria para cargar la información solicitada.",
    "idMedioRecepcion": 1,
    "idModalidadEntrega": 10,
    "datosUser": {
        "dsNameRole": "PNT- USUARIO SOLICITANTE",
        "id": 39039491,
        "idOrganoGarante": 0,
        "idSujetoObligado": -1,
        "idComite": -1,
        "idSubenlace": -1,
        "idUnidadAdministrativa": -1,
        "email": "contacto.ocamis@cipps.unam.mx",
        "nombUsuario": "Berenice",
        "apePatUsuario": "Cruz",
        "apeMatUsuario": "Maya",
        "roleId": 94728,
        "idMenu": 2
    }
}


example_response = {
    "statusCode": 0,
    "statusDescription": null,
    "errorMessage": null,
    "listaExitosos": [
        {
            "folio": "330018024012137",
            "dsUrlArchivo": null,
            "idOrganoGarante": 33,
            "dsOrganoGarante": "Federación",
            "exitoso": true,
            "nombreArchivo": null,
            "idSolGral": 9156229,
            "idSolicitudDependencia": 9558524
        }
    ],
    "listaEnProceso": []
}
