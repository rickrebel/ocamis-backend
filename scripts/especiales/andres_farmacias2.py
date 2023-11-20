import csv
import re
states = [
        "Aguascalientes",
        "Baja California",
        "Baja California Sur",
        "Campeche",
        "Coahuila de Zaragoza",
        "Colima",
        "Chiapas",
        "Chihuahua",
        "CIUDAD DE MÉXICO",
        "Durango",
        "Guanajuato",
        "Guerrero",
        "Hidalgo",
        "Jalisco",
        "México",
        "Michoacán de Ocampo",
        "Morelos",
        "Nayarit",
        "Nuevo León",
        "Oaxaca",
        "Puebla",
        "Querétaro Arteaga",
        "Quintana Roo",
        "San Luis Potosí",
        "Sinaloa",
        "Sonora",
        "Tabasco",
        "Tamaulipas",
        "Tlaxcala",
        "Veracruz de Ignacio de la Llave",
        "Yucatán",
        "Zacatecas"]


def read_pdf_table():
    import camelot
    file_path = "fixture/especiales/farmacia_sample.pdf"
    abc = camelot.read_pdf(file_path, pages="all")
    print(abc[0].df)



def read_pdf():
    # from PyPDF2 import PdfReader
    # reader = PdfReader(file_path)
    # page = reader.pages[0]
    # text = page.extract_text()
    # print(text)



def split_data(file_path="fixture/especiales/farmacias.txt"):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.readlines()
    data = []
    entry = []
    for line in content:
        entry.append(line.strip().upper())
        # REGEX of: hemoderivados) 2209095006D00056 2022-08-01 09:00:00.000
        # if re.match(r"^\d{10} \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}$", line):
        # if re.match(r"\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d+$", line):
        if re.match(r".*\s\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3}", line):
            data.append(entry)
            entry = []
    if entry:  # Añadimos el último registro si existe
        data.append(entry)
    return data


def process_data(data, limit=None):
    structured_data = []
    re_init = re.compile(r"^(?P<propietario>.+?)"
                         r"(?P<rfc>[A-Za-z]{3,4}\s?\d{6}([A-Za-z0-9]{3})?)\s"
                         r"(?P<name>.*)$")
    # re_cp = re.compile(r"(\s|^)(?P<cp>\d{5})\s(?P<geo>[A-Z\s]+)$")
    # re_cp = re.compile(r"(?:(\s)|^)(?P<cp>\d{5})\s(?P<geo>[A-Za-z\s]+)$")
    re_cp = re.compile(r"(?:(\s)|^)(?P<cp>\d{5})\s(?P<geo>.+)$")
    # numbers to regex: 623011, 464111, 464112, 464113
    re_numbers = re.compile(r"(?P<number>623011|464111|464112|464113)\s?:(?:\s|$)")
    re_id_and_date = re.compile(
        r".*\s(?P<id>[A-Z0-9]{14,16})\s"
        r"(?P<date>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3})$")
    # all_fields = propietario, rfc, name, cp, geo, special_numbers, numero_ingreso,
    #          f_tramite
    all_fields = ["propietario", "rfc", "name", "cp", "geo", "special_numbers",
                  "numero_ingreso", "f_tramite"]

    if limit:
        data = data[:limit]
    for entry in data:
        # Propietario y RFC
        propietario_data = []
        propietario = ""
        rfc = ""
        name = ""
        current_line = 1
        for x in range(0, len(entry)):
            first_match = re_init.match(entry[x])
            if first_match:
                for y in range(0, x):
                    propietario_data.append(entry[y])
                propietario_data.append(first_match.group("propietario"))
                propietario = " ".join(propietario_data).strip()
                rfc = first_match.group("rfc").replace(" ", "")
                name = first_match.group("name")
                current_line = x
        if not propietario or not rfc or not name:
            print("Error en propietario, rfc o name")
            print(entry)
            continue

        cp = None
        geo = None

        special_numbers = []
        for x in range(0, len(entry)):
            cp_match = re_cp.search(entry[x])
            if cp_match:
                cp = cp_match.group("cp")
                geo = cp_match.group("geo")
                current_line = x
                if not cp:
                    print("algo raro", entry[x])
                break

        for x in range(current_line, len(entry) - 1):
            special_match = re_numbers.match(entry[x])
            if special_match:
                special_numbers.append(special_match.group("number"))
        special_numbers = ", ".join(special_numbers)

        last_line = entry[-1]
        id_and_date_match = re_id_and_date.match(last_line)
        numero_ingreso = None
        f_tramite = None
        if id_and_date_match:
            numero_ingreso = id_and_date_match.group("id")
            f_tramite = id_and_date_match.group("date")

        current_data = []
        error_fields = []
        for field in all_fields:
            value = locals()[field]
            current_data.append(str(value))
            if not value:
                error_fields.append(field)
        if error_fields:
            print(f"Error en {error_fields}: \n{entry}")
        structured_data.append(current_data)

    return structured_data


def save_to_csv(data):
    path_save = 'fixture/especiales/cleaned_farmacias.csv'
    with open('fixture/especiales/cleaned_farmacias.csv', 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(
            ["PROPIETARIO", "RFC", "NOMBRE ESTABLECIMIENTO", "CP", "GEO",
             "ESPECIALES", "NUMERO DE INGRESO", "FECHA DE TRAMITE"])
        writer.writerows(data)


if __name__ == "__main__":
    raw_data = split_data("fixture/especiales/farmacias.txt")
    final_data = process_data(raw_data, 200)
    save_to_csv(final_data)












def import_txt(init_delete=False):
    file_path = 'fixture/especiales/farmacias.txt'
    f = open(file_path)
    seq = 0
    for row in f:
        seq += 1
        if seq > 10:
            break


def import_txt2():
    import io
    import csv
    file_path = 'fixture/especiales/farmacias.txt'
    try:
        with io.open(file_path, "r", encoding="utf-8") as file:
            data = file.read()
            file.close()
    except Exception as e:
        print(e)
        return False, ["%s" % (e)], False
    rr_data_rows = data.split("\n")
    last_botica = False
    final_data = []
    all_row = []
    def replace_text(s, old, new):
        li = s.rsplit(old, 1)
        return new.join(li)
    for row in rr_data_rows:
        if last_botica:
            all_row.append(row)
            if "ACTIVO" in row:
                row = " ".join(all_row)
                final_row = []
                splited = row.split(" ")
                final_row.append(splited[0])
                final_row.append(splited[1])
                rest_row = row[26:-7]
                for state in states:
                    state_upper = state.upper()
                    if state_upper in rest_row:
                        both = replace_text(rest_row, state_upper, "| %s" % state_upper)
                        both_splited = both.split(" | ")
                        if len(both_splited) > 1 and len(both_splited[1]) <= len(state_upper):
                            final_row += both_splited
                            final_data.append(final_row)
                            break
                else:
                    print("No logramos ninguna entidad")
                    print(rest_row)
                    print(row)
                    print("---------")
                last_botica = False
                all_row = []
        else:
            if row == 'BOTICA':
                last_botica = True
    csv_path = 'fixture/finallatin.csv'
    with open(csv_path, 'w', encoding="latin-1", newline="") as csv_file:
        write = csv.writer(csv_file, delimiter='|')
        write.writerows(final_data)
        csv_file.close()







examples2 = [
    "sureste S.A. DE C.V. CFS 950529980 sfa Irapuato Guanajuato ii"
]

re_init_ex = re.compile(r"^(?P<propietario>[A-Za-z\s\.]+?)(?P<rfc>[A-Za-z]{3,4}\s?\d{6}[A-Za-z0-9]{3})\s(?P<name>.*)$")

for example in examples2:
    match = re_init_ex.match(example)
    if match:
        print(match.group("propietario"))
        print(match.group("rfc"))
        print(match.group("name"))
    else:
        print("No match")

examples3 = [
    "464113: Comercio al por menor de productos"
]

re_numbers_ex = re.compile(r"(?P<number>623011|464111|464112|464113)\s?:(?:\s|$)")

for example in examples3:
    match = re_numbers_ex.match(example)
    if match:
        print(match.group("number"))
    else:
        print("No match")

examples4 = [
    "complementos alimienticios) 220201506D0148 2022-08-01 11:14:00.000"
]

re_id_and_date_ex = re.compile(r".*\s(?P<id>\d{4}[A-Z0-9]{10})\s(?P<date>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3})$")

for example in examples4:
    match = re_id_and_date_ex.match(example)
    if match:
        print(match.group("id"))
        print(match.group("date"))
    else:
        print("No match")

examples = [
   "GUTIERREZ OCHOA BETZABE GUOB611207E57 DISTRIBUCION PRODUCTOS DE CAFE DXN VALLARTA DIA 111 COL. VIDA VALLARTA 48318 PUERTO VALLARTA JALISCO",
   "464113: COMERCIO AL POR MENOR DE PRODUCTOS",
   "NATURISTAS, MEDICAMENTOS HOMEOPÁTICOS Y DE",
   "COMPLEMENTOS ALIMENTICIOS (INCLUYE FARMACIAS",
   "HOMEOPATICAS CON PREPARACIÓN DE",
   "ESPECIALIDADES FARMACÉUTICAS)(EXCEPTO ALIMENTOS",
   "Y COMPLEMENTOS ALIMIENTICIOS) , 433210:",
   "COMERCIO AL POR MAYOR DE ARTÍCULOS DE PERFUMERÍA",
   "Y COSMÉTICOS, 431199: COMERCIO AL POR MAYOR DE",
   "OTROS ALIMENTOS (INCLUYE SUPLEMENTOS",
   "ALIMENTICIOS) 221408518X1861 2022-08-01 08:26:00.000"
]
re_cp_example = re.compile(r"(?:(\s)|^)(?P<cp>\d{5})\s(?P<geo>.+)$")
# re_cp_example = re.compile(r"(?P<cp>\d{5})\s(?P<geo>.+)$")
# re_cp_example = re.compile(r"(?:(\s)|^)(?P<cp>\d{5})\s(?P<geo>[A-Za-z\s]+)$")
# re_cp_example = re.compile(r"(?P<cp>\d{5})\s(?P<geo>[A-Za-z\s]+)$")

for example in examples:
    cp_match = re_cp_example.search(example)
    if cp_match:
        print("cp-geo: ", cp_match.group("cp"), "|", cp_match.group("geo"))
    else:
        print("No match")

# 2209155007D00007
# 221403506D0606
# 07330021182392
# 093300515A1188
# 123300EL950683
# 163300109C4447
# 173300503X0025
# 2315175006D00009
