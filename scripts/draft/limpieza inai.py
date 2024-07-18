#Ejemplo para probar funcion que prueba txt
def test_data_from_file():
    #path_imss = "C:\\Users\\iakar\\Desktop\\desabasto\\pruebas_scripts\\req_septiembre_2020_02_1.txt"
    path_imss = "C:\\Users\\Ricardo\\Desktop\\experimentos\\SOLICITUDES_33_2022_19296.json"
    number_columns = 14
    row_start_data = 1
    row_headers = None
    final_data, headers, error_number_columns = get_info_from_txt(
        path_imss, number_columns, row_start_data, row_headers)
    # print("rows_count: ", len(final_data)) ## 1,000,000
    # print("headers: ", headers) ## None
    # print("error_number_columns: ", error_number_columns) ## 0
    # print("primeros datos:\n", final_data[:20]) ## [[----],[----],...]


def get_info_from_txt(
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
        return False, ["%s" % (e)], False
    txt_rows = data.replace("\r\n","\n")
    # txt_rows = data.split("\n")
    final_data = []
    headers = None
    error_number_columns = 0
    for index, data_row in enumerate(txt_rows):
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
    import re
    import json
    data = None
    rr_txt_rows = None
    # path_json = "C:\\Users\\Ricardo\\Desktop\\experimentos\\sol19296_0.json"
    path_json = "fixture/pruebas/SOLICITUDES_AGS.json"
    with io.open(path_json, "r", encoding="latin-1") as file:
        data = file.read()
        file.close()

    # data_json = data.replace('\r', '').replace('\n', '')
    # between { and }
    final_lines = []
    pattern_lines = r'{"Folio":(.*?)}'
    # Between DescripcionSolicitud & FechaRespuesta
    matches = re.findall(pattern_lines, data)
    second_pattern = r'^(.*?)"DescripcionSolicitud":"(.*?)","FechaRespuesta":"(.*)"$'
    second_pattern = re.compile(second_pattern)
    example = None
    json_data = []

    for match in matches:
        # print(match)
        try:
            line_matches = second_pattern.findall(match)[0]
            between = line_matches[1]
            between = between.replace("\"", "*")
            final_line = (f'"Folio":{line_matches[0]}'
                          f'"DescripcionSolicitud":"{between}",'
                          f'"FechaRespuesta":"{line_matches[2]}"')
            # final_lines.append("{" + final_line + "}")
        except Exception as e:
            print(f"Error extraño: {e}")
            print(match)
            example = match
            break
        try:
            json_line = json.loads('{' + final_line + '}')
            json_data.append(json_line)
        except Exception as e:
            print(f"Error en json: {e}")
            print(final_line)
            break

    final_data = "[" + ",".join(final_lines) + "]"
    json_data = json.loads(final_data)

    data_file = data.replace("\n", "\\n")
    # Lo que está fuera
    # rr_txt_rows = json.load(file)
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

        
def adivinar_nombre():
    import re
    from geo.models import Agency

    unique_agencies = [
        'Centro Regional de Alta Especialidad de Chiapas (CRAE)',
        'Instituto de Seguridad y Servicios Sociales de los Trabajadores del Estado (ISSSTE)',
        'Instituto Mexicano del Seguro Social (IMSS)',
        'Instituto Nacional de Cancerología (INCAN)',
        'Instituto Nacional de Cardiología Ignacio Chávez (INCAR)',
        'Instituto Nacional de Ciencias Médicas y Nutrición Salvador Zubirán (INNSZ)',
        'Instituto Nacional de Enfermedades Respiratorias Ismael Cosío Villegas (INER)',
        'SSA-Instituto Nacional de Geriatría (*)',
        'Instituto Nacional de las Personas Adultas Mayores (INAPAM)',
        'Instituto Nacional de Medicina Genómica (INMEGEN)',
        'Instituto Nacional de Neurología y Neurocirugía Manuel Velasco Suárez (INNN)',
        'Instituto Nacional de Pediatría (INP)',
        'Instituto Nacional de Perinatología Isidro Espinosa de los Reyes (INPER)',
        'Instituto Nacional de Psiquiatría Ramón de la Fuente Muñiz (INPRFM)',
        'Instituto Nacional de Rehabilitación Luis Guillermo Ibarra Ibarra (INR)',
        'Instituto Nacional de Salud Pública (INSP)',
        'Hospital General "Dr. Manuel Gea González" (HOSPITAL GEA)',
        'Hospital General de México "Dr. Eduardo Liceaga" (HGM)',
        'Hospital Infantil de México Federico Gómez (HIMFG)',
        'Hospital Juárez de México (HJM',
        'Hospital Regional de Alta Especialidad de Ciudad Victoria "Bicentenario 2010" (HRAEV)',
        'Hospital Regional de Alta Especialidad de Ixtapaluca (HRAEI)',
        'Hospital Regional de Alta Especialidad de la Península de Yucatán (HRAEPY)',
        'Hospital Regional de Alta Especialidad de Oaxaca (HRAEO)',
        'Hospital Regional de Alta Especialidad del Bajío (HRAEB)',
        'Sindicato Único de Trabajadores del Instituto Nacional de Perinatología (SUTINPER)',
        'INSABI-Fondo de Salud para el Bienestar',
        'Instituto de Salud para el Bienestar',
    ]

    for agency in unique_agencies:
        match = re.search(r"\(([a-zA-Z]+?)\)", agency)
        if match:
            first_text_between_parentheses = match.group(1)
            try:
                agency_obj = Agency.objects.get(acronym=first_text_between_parentheses)
                agency_obj.nameForInai = agency
                agency_obj.save()
            except Agency.DoesNotExist:
                continue
        else:
            print("No text between parentheses found.")


def delete_duplicates():
    from inai.models import Petition, PetitionBreak
    from category.models import DateBreak

    all_date_breaks = DateBreak.objects.all()
    all_petitions = Petition.objects.all()
    for petition in all_petitions:
        current_pet_breaks = PetitionBreak.objects.filter(petition=petition)
        for date_break in all_date_breaks:
            current_date_breaks = current_pet_breaks.filter(date_break=date_break)
            if current_date_breaks.count() > 1:
                last_pet_break = current_date_breaks.last()
                current_date_breaks.exclude(id=last_pet_break.id).delete()

