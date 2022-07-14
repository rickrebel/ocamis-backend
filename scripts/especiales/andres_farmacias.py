
def import_campaigns(init_delete=False):
    file_path = 'fixture/farmacias_andres.csv' 
    f = open(file_path)
    seq = 0
    for row in f:
        seq+=1
        if seq > 10:
            break

def import_campaigns2():
    import io
    import csv
    states = [
        "Aguascalientes",
        "Baja California",
        "Baja California Sur",
        "Campeche",
        "Coahuila de Zaragoza",
        "Colima",
        "Chiapas",
        "Chihuahua",
        "Ciudad de México",
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
    file_path = 'fixture/farmacias_andres.csv' 
    try:
        with io.open(file_path, "r", encoding="utf-8") as file:
            data = file.read()
            file.close()
    except Exception as e:
        print(e)
        return False, [u"%s" % (e)], False
    rr_data_rows = data.split("\n")
    last_botica = False
    final_data = []
    all_row = []
    def rreplace(s, old, new):
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
                        both = rreplace(rest_row, state_upper, "| %s" % state_upper)
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



