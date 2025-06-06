# -*- coding: utf-8 -*-
import json

import os

from desabasto.models import (
    CLUES,
    Container,
    DocumentType,
    Doctor,
    MedicalSpeciality,
    drug,
    Prescription,
)

from django.conf import settings
from django.db.models import Q
from django.utils.dateparse import parse_datetime

import psycopg2


especialidad_medico_list = {}
tipo_documento_list = {}
ISSSTE_ID = 4

dbname = "postgres"
user = "postgres"
password = "postgres"
host = "localhost"
port = 5432
constant_path = "C:\\git\\rick_\\Desktop\\nosotrxs\\issste\\"
script_dir = os.path.dirname(constant_path)
sep_cols = '|'
sep_rows = '\n'

data = ""
first_null = (
    "\n----------|------------------|-------------|---------------"
    "|--------------|--------------|---------------|-------------"
    "|-------------|-----------------|-----------------------"
    "|------------------|------------------|------------|-------------"
    "|-------------------|------------------|----")
year = '2019'
base_sql = (
    "COPY desabasto_recipereportraw(delegation,budget_key,"
    "unidad_medica,tipo_unidad_med,nivel_atencion,tipo_documento,"
    "folio_document,date_release,fecha_entrega,clave_medicamento,"
    "descripcion_medicamento,prescribed_amount,delivered_amount,"
    "clave,full_name,especialidad_medico,price,rn)")
base_sql2 = (
    "COPY desabasto_recipereportraw(delegation,budget_key,"
    "unidad_medica,tipo_unidad_med,nivel_atencion,tipo_documento,"
    "folio_document,date_release,fecha_entrega,clave_medicamento,"
    "descripcion_medicamento,prescribed_amount,delivered_amount,"
    "clave,full_name,especialidad_medico,price)")
options = "csv DELIMITER '|' NULL 'NULL' HEADER ENCODING 'LATIN1'"
options2 = "csv DELIMITER '|' NULL 'NULL' ENCODING 'LATIN1'"


def get_data(file="reporte_recetas_202011_4.csv", start_index=3, base_print=1):
    import csv
    # total_rows = 0
    error_len_row = []
    error_len_data = []
    try:
        date_name = int(file[16:22])
    except Exception as e:
        raise e
    with open(file) as File:
        # total_rows = len(File.readlines())
        pass
    with open(file) as File:
        reader = csv.reader(File)
        # headers = True
        x = 0
        for row in reader:
            x += 1
            if x < start_index:
                continue
            if x % base_print == 0:
                print(x)
            if len(row) != 1:
                # resultado inesperado, guardar x
                error_len_row.append(x)
                continue
            data = [d.strip() for d in row[0].split("|")]
            if len(data) != 18:
                error_len_data.append(x)
                continue
            delegation = data[0].decode('latin-1').encode("utf-8")
            budget_key = data[1].decode('latin-1').encode("utf-8")
            unidad_medica = data[2].decode('latin-1').encode("utf-8")
            tipo_unidad_med = data[3].decode('latin-1').encode("utf-8")
            nivel_atencion = data[4].decode('latin-1').encode("utf-8")
            tipo_documento = data[5].decode('latin-1').encode("utf-8")
            folio_document = data[6].decode('latin-1').encode("utf-8")
            date_release = data[7].decode('latin-1').encode("utf-8")
            fecha_entrega = data[8].decode('latin-1').encode("utf-8")
            clave_medicamento = data[9].decode('latin-1').encode("utf-8")
            descripcion_medicamento = data[
                10].decode('latin-1').encode("utf-8")
            prescribed_amount = data[11].decode('latin-1').encode("utf-8")
            delivered_amount = data[12].decode('latin-1').encode("utf-8")
            clave_doctor = data[13].decode('latin-1').encode("utf-8")
            nombre_medico = data[14].decode('latin-1').encode("utf-8")
            especialidad_medico = data[15].decode('latin-1').encode("utf-8")
            price = data[16].decode('latin-1').encode("utf-8")
            rn = data[17].decode('latin-1').encode("utf-8")
            try:
                recipe_report = Prescription.objects\
                    .filter(folio_document=folio_document).first()
                if not recipe_report:
                    recipe_report = Prescription()
                    recipe_report.year_month = date_name
                    clues, lost_ref = get_clues(
                        delegation=delegation,
                        budget_key=budget_key,
                        unidad_medica=unidad_medica,
                        tipo_unidad_med=tipo_unidad_med,)
                    recipe_report.clues = clues
                    recipe_report.lost_ref = lost_ref
                    recipe_report.tipo_documento = get_tipo_documento(
                        tipo_documento)
                    recipe_report.folio_document = folio_document
                    # recipe_report.date_release = datetime_format(
                    #     date_release)
                    # recipe_report.fecha_entrega = datetime_format(
                    #     fecha_entrega)
                    recipe_report.doctor = get_doctor(
                        clave_doctor=clave_doctor,
                        nombre_medico=nombre_medico,
                        especialidad_medico=especialidad_medico,)
                    if recipe_report.doctor:
                        recipe_report.especialidad_medico = recipe_report\
                            .doctor.especialidad_medico
                    recipe_report.save()
                drug = Drug()
                drug.recipereport = recipe_report
                # drug.date_release = datetime_format(date_release)
                # drug.fecha_entrega = datetime_format(fecha_entrega)
                drug.prescribed_amount = prescribed_amount
                drug.delivered_amount = delivered_amount
                drug.price = price
                drug.rn = rn
                container = Container.objects.filter(
                    Q(key2=clave_medicamento) |
                    Q(key=clave_medicamento)
                ).first()
                if container:
                    drug.container = container
                else:
                    drug.lost_ref = json.dumps({
                        "clave_medicamento": clave_medicamento,
                        "descripcion_medicamento": descripcion_medicamento,
                    })
                drug.save()
                # if x == 5:
                #     break
            except Exception as e:
                print("delegation")
                print(delegation)
                print
                print("budget_key")
                print(budget_key)
                print
                print("unidad_medica")
                print(unidad_medica)
                print
                print("tipo_unidad_med")
                print(tipo_unidad_med)
                print
                print("nivel_atencion")
                print(nivel_atencion)
                print
                print("tipo_documento")
                print(tipo_documento)
                print
                print("folio_document")
                print(folio_document)
                print
                print("date_release")
                print(date_release)
                print
                print("fecha_entrega")
                print(fecha_entrega)
                print
                print("clave_medicamento")
                print(clave_medicamento)
                print
                print("descripcion_medicamento")
                print(descripcion_medicamento)
                print
                print("prescribed_amount")
                print(prescribed_amount)
                print
                print("delivered_amount")
                print(delivered_amount)
                print
                print("clave")
                print(clave_doctor)
                print
                print("full_name")
                print(nombre_medico)
                print
                print("especialidad_medico")
                print(especialidad_medico)
                print
                print("price")
                print(price)
                print
                print("rn")
                print(rn)
                print
                print
                raise e


def get_clues(**kwargs):
    # delegation = kwargs.get("delegation")
    unidad_medica = kwargs.get("unidad_medica")
    clues_name = unidad_medica[unidad_medica.index(" "):].strip()
    clues_query = CLUES.objects.filter(
        name__icontains=clues_name, institution__id=ISSSTE_ID)
    clues = None
    if clues_query.count() == 1:
        clues = clues_query.first()
    lost_ref = None
    if not clues:
        lost_ref = json.dumps(kwargs)
    return clues, lost_ref


def get_doctor(**kwargs):
    clave_doctor = kwargs.get("clave")
    if clave_doctor == "NULL":
        return None
    nombre_medico = kwargs.get("full_name")
    especialidad_medico = kwargs.get("especialidad_medico")
    doctor = Doctor.objects.filter(clave_doctor=clave_doctor).first()
    if not doctor:
        doctor = Doctor()
        doctor.clave = clave_doctor
        doctor.full_name = nombre_medico
        if especialidad_medico in especialidad_medico_list:
            especialidad_medico = especialidad_medico_list.get(
                especialidad_medico)
        else:
            especialidad_medico, is_created = MedicalSpeciality.objects\
                .get_or_create(name=especialidad_medico)
            especialidad_medico_list[
                especialidad_medico.name] = especialidad_medico
        doctor.especialidad_medico = especialidad_medico
        doctor.save()
    return doctor


def get_tipo_documento(tipo_documento):
    if tipo_documento in tipo_documento_list:
        return tipo_documento_list.get(tipo_documento)
    tipo_documento, is_created = DocumentType.objects\
        .get_or_create(name=tipo_documento)
    tipo_documento_list[tipo_documento.name] = tipo_documento
    return tipo_documento


def datetime_format(datetime_str):
    datetime_date = parse_datetime(datetime_str)
    return datetime_date


def clean_special(data):
    message_final = 'sys.databases\n'
    idx_col = 0
    while True:
        try:
            idx_col = data.index('COLECTIVO|', idx_col + 80)
            idx_year = data.index("|%s" % year, idx_col, idx_col + 80)
            if "|" in data[idx_col + 10:idx_year]:
                print("hay un espacio de mas")
                curr_str = data[idx_col + 10:idx_year - 1]
                print(curr_str)
                curr_done = curr_str.replace("|", "-")
                next_data = data[idx_col:idx_col + 6000]
                cleaned_current = next_data.replace(curr_str, curr_done)
                data = "%s%s%s" % (
                    data[:idx_col], cleaned_current, data[idx_col + 6000:])
            else:
                pass
        except Exception:
            break
    while True:
        try:
            idx_msg = data.index('Mensaje 9002')
            idx_msg2 = data.index(message_final, idx_msg)
            print("----------")
            print(data[idx_msg:idx_msg2 + len(message_final)])
            data = "%s%s" % (data[:idx_msg],
                             data[idx_msg2 + len(message_final):])
        except Exception:
            break
    fabian = 'FABIAN ZARATE GALINDO|'
    fabian2 = 'FABIAN ZARATE GALINDO||'
    if fabian2 in data:
        print("caso FABIAN")
        data = data.replace(fabian2, fabian)
    return data


def special_coma(all_data):
    rows = all_data.split("\n")
    count = 0
    final_rows = []
    for idx, row in enumerate(rows):
        new_row = row.replace('1,114 gr.', '1$114 gr.')\
            .replace('0,000', '0$000').replace('VERACRUZ,VER', 'VERACRUZ$VER')\
            .replace(' VEGA,CULIAC', 'VEGA$CULIAC')\
            .replace(' PUCHADES,TEPIC', 'PUCHADES$TEPIC')
        cols = new_row.split(",")
        len_cols = len(cols)
        if len_cols == 17:
            final_rows.append(sep_cols.join(cols).replace('$', ","))
        elif len_cols > 17:
            new_row = new_row.replace(
                ',',
                '|').replace(
                '| ',
                ', ').replace(
                '$',
                ",")
            cols = new_row.split(sep_cols)
            len_cols = len(cols)
            if len_cols == 16:
                clave = cols[13].replace(', ', ',').split(",")
                cols = sep_cols.join(cols[:13] + clave + cols[14:])
                final_rows.append(cols)
            elif len_cols == 17:
                final_rows.append(new_row)
            elif len_cols > 17:
                count += 1
                if count < 20:
                    print("--------------------")
                    print("error 1")
                    print(idx)
                    print(row)
                    # break
                # print (new_row)
                # for col in cols:
                #    print (col)
            else:
                count += 1
                print("error 2")
                print(row)
                # break
        else:
            print("error 3")
            print(row)
            break
    print("especial coma %s errores" % count)
    all_data = sep_rows.join(final_rows)
    return all_data


def converter_file_in_related_files(
        file_path, year_month=0,
        clean_data=True, update_files=True,
        recipe_path="test_recipe.csv",
        medicine_path="test_medicine.csv"):
    from desabasto.models import Prescription
    with_coma = False
    try:
        with open(file_path) as file:
            data = file.read()
            if "|" not in data[:3000]:
                with_coma = True

            if clean_data:
                if with_coma:
                    data = special_coma(data)
                data = data.replace("\"", "").replace(first_null, "")
                data = clean_special(data)
            file.close()
    except Exception as e:
        print(e)
        return

    rows = data.split("\n")

    if not with_coma:
        headers = rows.pop(0)
        print("se quito heades del procesado: ", headers)
    recipe_first = rows[0].split("|")

    recipes_data = {}

    if len(recipe_first) >= 17:
        first_folio = recipe_first[6]
        previus_recipe = Prescription.objects\
            .filter(folio_document=first_folio).first()
        if previus_recipe:
            recipes_data[first_folio] = {
                "id": previus_recipe.id,
                "medicines": [],
                "exist": True,
                "delivered_medicine": []
            }
    x = 0
    artificial_id = last_recipe_id + 1
    data_file_recipe = []
    data_file_medicine = []
    for row in rows:
        x += 1
        recipe_report_data = row.split("|")

        if len(recipe_report_data) < 17:
            print(x)
            print("esta fila no tiene los datos suficientes")
            continue
        delegation = recipe_report_data[0]
        budget_key = recipe_report_data[1]
        unidad_medica = recipe_report_data[2]
        tipo_unidad_med = recipe_report_data[3]
        nivel_atencion = recipe_report_data[4]
        tipo_documento = recipe_report_data[5]
        folio_document = recipe_report_data[6]
        date_release = recipe_report_data[7]
        fecha_entrega = recipe_report_data[8]
        clave_medicamento = recipe_report_data[9]
        # descripcion_medicamento = recipe_report_data[10]
        prescribed_amount = recipe_report_data[11]
        delivered_amount = recipe_report_data[12]
        clave_doctor = recipe_report_data[13]
        nombre_medico = recipe_report_data[14]
        especialidad_medico = recipe_report_data[15]
        price = recipe_report_data[16]
        if with_coma:
            rn = "NULL"
        else:
            rn = recipe_report_data[17]

        if folio_document not in recipes_data:
            recipes_data[folio_document] = {
                "id": artificial_id,
                "delegation": delegation,
                "budget_key": budget_key,
                "unidad_medica": unidad_medica,
                "tipo_unidad_med": tipo_unidad_med,
                "nivel_atencion": nivel_atencion,
                "tipo_documento": tipo_documento,
                "folio_document": folio_document,
                "clave": clave_doctor,
                "full_name": nombre_medico,
                "especialidad_medico": especialidad_medico,
                "delivered_medicine": []
            }
            artificial_id += 1

        # convertir datos a enteros
        calculate_delivered = True
        if (prescribed_amount or "").isdigit():
            prescribed_amount = int(prescribed_amount)
        else:
            calculate_delivered = False
            prescribed_amount = "NULL"

        #
        if (delivered_amount or "").isdigit():
            delivered_amount = int(delivered_amount)
        else:
            calculate_delivered = False
            delivered_amount = "NULL"
        # ---------------------------
        if calculate_delivered:
            # calculo de delivered
            if delivered_amount:
                if prescribed_amount == delivered_amount:
                    delivered_type = "all"
                else:
                    delivered_type = "ptl"
            else:
                delivered_type = "no"
        else:
            delivered_type = "NULL"

        medicine_row = [
            recipes_data[folio_document]["id"],
            date_release,
            fecha_entrega,
            clave_medicamento,
            prescribed_amount,
            delivered_amount,
            price,
            rn,
            delivered_type
        ]

        data_file_medicine.append(medicine_row)
        recipes_data[folio_document]["delivered_medicine"]\
            .append(delivered_type)

    print("se termino de leer todas las lineas")

    for folio_document, recipe_data in recipes_data.items():
        if recipe_data.get("exist"):
            continue
        delivered_medicine = recipe_data.get("delivered_medicine")
        if not delivered_medicine:
            recipe_delivered = "NULL"
        else:
            if all([delivered == "all" for delivered in delivered_medicine]):
                recipe_delivered = "all"
            elif all([delivered == "no" for delivered in delivered_medicine]):
                recipe_delivered = "no"
            else:
                recipe_delivered = "ptl"

        data_file_recipe.append([
            recipe_data.get("id"),
            year_month,
            recipe_data.get("id"),
            recipe_data.get("delegation"),
            recipe_data.get("budget_key"),
            recipe_data.get("unidad_medica"),
            recipe_data.get("tipo_unidad_med"),
            recipe_data.get("nivel_atencion"),
            recipe_data.get("tipo_documento"),
            recipe_data.get("folio_document"),
            recipe_data.get("clave"),
            recipe_data.get("full_name"),
            recipe_data.get("especialidad_medico"),
            recipe_delivered])

    print("se termino de calcular los objetos recipe")

    import csv
    with open(recipe_path, 'wb') as file:
        # using csv.writer method from CSV package
        write = csv.writer(file, delimiter='|')
        write.writerows(data_file_recipe)
        file.close()

    with open(medicine_path, 'wb') as file:
        # using csv.writer method from CSV package
        write = csv.writer(file, delimiter='|')
        write.writerows(data_file_medicine)
        file.close()

    if update_files:
        upload_csv_to_database(
            recipe_path, "desabasto_recipereport",
            ("id", "year_month", "calculate_id", "delegation",
                "budget_key", "unidad_medica", "tipo_unidad_med",
                "nivel_atencion", "tipo_documento", "folio_document",
                "clave", "full_name", "especialidad_medico",
                "delivered", ))

        upload_csv_to_database(
            medicine_path, "desabasto_recipemedicine",
            ("recipe_id", "date_release", "fecha_entrega",
                "clave_medicamento", "prescribed_amount",
                "delivered_amount", "price", "rn", "delivered",
             ))


def upload_csv_to_database(file_path, table_name, columns):
    f = open(file_path)
    import os
    base_dir = os.path.dirname(os.path.dirname(__file__))

    columns_join = ",".join(columns)
    options = "csv DELIMITER '|' NULL 'NULL' ENCODING 'LATIN1'"
    sql = "COPY %s(%s) FROM '%s\\%s' %s;" % (
        table_name, columns_join, base_dir, file_path, options)

    desabasto_conection = getattr(settings, "DATABASES").get("desabasto_db")
    con = psycopg2.connect(
        database=desabasto_conection.get("NAME"),
        user=desabasto_conection.get("USER"),
        password=desabasto_conection.get("PASSWORD"),
        host=desabasto_conection.get("HOST"),
        port=desabasto_conection.get("PORT"))
    cur = con.cursor()
    try:
        cur.copy_expert(sql, f)
        # with open("%s_done" % file_path, 'wb') as file:
        #     file.write('done')
        # os.remove("%s\\%s" % (script_dir, origin_path))
    except Exception as e:
        print(e)
        con.close()
        f.close()
        return
    con.commit()
    con.close()
    f.close()


def massive_upload_csv_to_db(path="", years=['2019', '2020', '2021']):
    for year in years:
        for mon in xrange(12):
            month = mon + 1
            base_path = "%s%s%s" % (year, '0' if month < 10 else '', month)
            for file_num in xrange(8):
                curr_path = "reporte_recetas_%s_%s.csv" % (
                    base_path, file_num + 1)
                recipe_path = "recipe_%s" % (curr_path)
                medicine_path = "medicine_%s" % (curr_path)
                if path:
                    hash_dir = "" if path[-1] == "\\" else "\\"
                    curr_path = "%s%s%s" % (path, hash_dir, curr_path)
                    recipe_path = "%s%s%s" % (path, hash_dir, recipe_path)
                    medicine_path = "%s%s%s" % (path, hash_dir, medicine_path)

                # #curr_path = "201908_1.csv"
                print(curr_path)
                converter_file_in_related_files(
                    curr_path, year_month=base_path,
                    recipe_path=recipe_path,
                    medicine_path=medicine_path)
                print
