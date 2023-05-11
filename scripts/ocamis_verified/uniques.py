from django.db import connection
from task.aws.common import calculate_delivered_final
from datetime import datetime

group_names = ["dupli", "shared"]


def get_all_folios(filters):
    cursor = connection.cursor()
    entity_id = filters["entity_id"]
    year = filters["year"]
    week = filters["week"]
    sql_query = f"""
        SELECT
            drug.sheet_file_id AS sheet_id,
            drug.prescription_id AS uuid_folio,
            pres.folio_ocamis as folio_ocamis,
            pres.month as month
        FROM
            formula_prescription pres
            INNER JOIN formula_drug drug ON pres.uuid_folio = drug.prescription_id
            RIGHT JOIN (
                SELECT
                    sheetfile.id
                FROM
                    inai_sheetfile sheetfile
                    INNER JOIN inai_datafile datafile ON sheetfile.data_file_id = datafile.id
                WHERE
                    sheetfile.behavior_id != 'invalid' AND
                    datafile.entity_id = {entity_id}
            ) AS sf ON drug.sheet_file_id = sf.id            
        WHERE
            pres.entity_id = {entity_id} AND
            pres.iso_week = {week} AND
            pres.iso_year = {year}
    """
    cursor.execute(sql_query)
    every_folios = {}
    all_drugs = cursor.fetchall()
    len_drugs = len(all_drugs)
    if len_drugs:
        print("all_drugs", len_drugs)
    for idx in range(len_drugs):
        drug = all_drugs.pop()
        sheet_id, uuid_folio, folio_ocamis, month = drug
        uuid_and_sheet = (uuid_folio, sheet_id, month)
        # folio_ocamis = drug[1]
        # if folio_ocamis not in every_folios:
        #     every_folios[folio_ocamis] = {sheet_id}
        if folio_ocamis not in every_folios:
            every_folios[folio_ocamis] = {uuid_and_sheet}
        else:
            every_folios[folio_ocamis].add(uuid_and_sheet)
    len_folios = len(every_folios)
    if len_folios:
        print("every_folios", len_folios)
    cursor.close()
    return every_folios


def get_duplicate_folios(filters):
    all_folios = get_all_folios(filters)
    current_month = filters["month"]
    totals_by_sheet = {}
    month_counts = {"dupli": 0, "shared": 0, "total": 0}
    folios = {"dupli": {}, "shared": {}}
    # for folio in all_folios.keys():
    for folio_ocamis, values in all_folios.items():
        # values = all_folios.pop(folio)
        # sheets_count = len(values)
        # sheets_count = 0
        is_same_month = False
        current_sheets = set()
        current_uuid = set()
        for uuid_folio, sheet_id, month in values:
            current_sheets.add(sheet_id)
            current_uuid.add(uuid_folio)
            if not is_same_month:
                is_same_month = current_month == int(month)
        if is_same_month:
            month_counts["total"] += 1
        len_uuids = len(current_uuid)
        len_sheets = len(current_sheets)
        if len_sheets > 1:
            group_name = "shared" if len_uuids == 1 else "dupli"
            folios[group_name][folio_ocamis] = current_sheets
            if is_same_month:
                month_counts[group_name] += 1
        for sheet_id in current_sheets:
            shared_plus = 0
            duplicates_plus = 0
            if len_sheets > 1:
                if len_uuids == 1:
                    shared_plus = 1
                elif len_uuids > 1:
                    duplicates_plus = 1
            if sheet_id not in totals_by_sheet:
                totals_by_sheet[sheet_id] = {
                    "total": 1,
                    "dupli": duplicates_plus,
                    "shared": shared_plus}
            else:
                totals_by_sheet[sheet_id]["total"] += 1
                totals_by_sheet[sheet_id]["shared"] += shared_plus
                totals_by_sheet[sheet_id]["dupli"] += duplicates_plus
    return folios, totals_by_sheet, month_counts


def get_pairs(input_list):
    from itertools import combinations
    return list(combinations(input_list, 2))


def build_pairs_sheets(filters):
    folios, sheets, month_counts = get_duplicate_folios(filters)
    # SPACE
    def build_small_pairs(input_dict, input_name):
        len_input = len(input_dict)
        if len_input:
            print(input_name, len_input)
        every_pairs = {}
        for folio, sheet_ids in input_dict.items():
            sheet_ids = sorted(sheet_ids)
            current_pairs = get_pairs(sheet_ids)
            for pair in current_pairs:
                if pair not in every_pairs:
                    every_pairs[pair] = 1
                else:
                    every_pairs[pair] += 1
        len_pairs = len(every_pairs)
        if len_pairs:
            print(input_name, len_pairs)
        return every_pairs
    pairs = {}
    for group_name in group_names:
        pairs[group_name] = build_small_pairs(folios[group_name], group_name)
    # dupli = folios["dupli"]
    # shared = folios["shared"]
    # dupli_pairs = build_small_pairs(dupli, "dupli")
    # shared_pairs = build_small_pairs(shared, "shared")
    # pairs = {"dupli": dupli_pairs, "shared": shared_pairs}
    # return dupli_pairs, shared_pairs, sheets
    return pairs, sheets, month_counts


def save_sheets_months(filters, month_counts):
    from inai.models import MonthAgency
    entity_id = filters["entity_id"]
    year_month = f"{filters['year']}-{str(filters['month']).zfill(2)}"
    current_month_entities = MonthAgency.objects.filter(
        entity_id=entity_id, year_month=year_month)
    current_month_entities.update(
        duplicates_count=month_counts["dupli"],
        shared_count=month_counts["shared"],
        prescriptions_count=month_counts["total"]
    )


# def save_crossing_sheets(entity_id, dupli_pairs, shared_pairs, sheets):
def save_crossing_sheets(filters, entity_id, month_pairs, sheets):
    from django.utils import timezone
    from inai.models import CrossingSheet, SheetFile
    # SPACE
    shared_pairs = month_pairs["shared"]
    month = filters["month"]
    year = filters["year"]
    year_month = f"{year}-{str(month).zfill(2)}"
    edited_crosses = []
    # SPACE
    for sheet_id, value in sheets.items():
        current_sheet = SheetFile.objects.get(id=sheet_id)
        if current_sheet.year_month != year_month:
            continue
        current_sheet.prescriptions_count = value["total"]
        current_sheet.duplicates_count = value["dupli"]
        current_sheet.shared_count = value["shared"]
        current_sheet.save()
    # SPACE
    def same_year_month(cr):
        year_months = [cr.sheet_file_1.year_month, cr.sheet_file_2.year_month]
        some_is_same = year_month in year_months
        if some_is_same:
            edited_crosses.append(cr.id)
        return some_is_same
    # SPACE
    already_shared = set()
    for pair, value in month_pairs["dupli"].items():
        # shared_count = shared_pairs.pop(pair, 0)
        cross, created = CrossingSheet.objects.get_or_create(
            entity_id=entity_id,
            sheet_file_1_id=pair[0],
            sheet_file_2_id=pair[1],
        )
        if not same_year_month(cross):
            continue
        shared_count = shared_pairs.get(pair, 0)
        if shared_count:
            already_shared.add(pair)
        # SPACE
        cross.duplicates_count = value
        cross.shared_count = shared_count
        cross.last_crossing = timezone.now()
        if not created:
            print("cross", cross)
            print("last_crossing", cross.last_crossing)
            print("!!!!!!!!!!!!!!!!!!!!!\n")
        cross.save()
    # SPACE
    for pair, value in shared_pairs.items():
        if pair in already_shared:
            continue
        cross, created = CrossingSheet.objects.get_or_create(
            entity_id=entity_id,
            sheet_file_1_id=pair[0],
            sheet_file_2_id=pair[1]
        )
        if not same_year_month(cross):
            continue
        cross.duplicates_count = 0
        cross.shared_count = value
        cross.last_crossing = timezone.now()
        cross.save()
    # SPACE
    year_month_crosses_1 = CrossingSheet.objects.filter(
        entity_id=entity_id, sheet_file_1__year_month=year_month)
    year_month_crosses_2 = CrossingSheet.objects.filter(
        entity_id=entity_id, sheet_file_2__year_month=year_month)
    year_month_crosses = year_month_crosses_1 | year_month_crosses_2
    year_month_crosses = year_month_crosses.exclude(id__in=edited_crosses)
    year_month_crosses.delete()

# -----------------------------
# -----------------------------
# -----------------------------
# -----------------------------


def get_uuids_duplicates(filters):
    print("start get_uuids_duplicates", datetime.now())
    cursor = connection.cursor()
    entity_id = filters["entity_id"]
    week = filters["week"]
    month = filters["month"]
    year = filters["year"]
    month_str = str(month).zfill(2)
    # year_month = f"{year}-{month_str}"
    # SPACE
    create_temp_table = f"""
        CREATE TEMP TABLE merge_sheetfiles AS
        SELECT
            sheetfile.id
        FROM
            inai_sheetfile sheetfile
            JOIN inai_datafile datafile ON sheetfile.data_file_id = datafile.id
        WHERE
            (sheetfile.behavior_id = 'need_merge' OR sheetfile.behavior_id = 'merged') AND
            datafile.entity_id = {entity_id}
    """
    cursor.execute(create_temp_table)
    # SPACE
    sql_query = f"""
        SELECT
            drug.sheet_file_id AS sheet_id,
            pres.folio_ocamis as folio_ocamis,
            pres.uuid_folio as uuid_folio,
            pres.delivered_final_id as delivered
        FROM
            formula_prescription pres
            INNER JOIN formula_drug drug ON pres.uuid_folio = drug.prescription_id
            INNER JOIN merge_sheetfiles sheetfile ON drug.sheet_file_id = sheetfile.id        
        WHERE 
            pres.entity_id = {entity_id} AND
            pres.iso_week = {week} AND
            pres.iso_year = {year}
    """
    cursor.execute(sql_query)
    every_folios = {}
    for_edit_folios = set()
    for_edit_delivered = set()
    all_drugs = cursor.fetchall()
    print("all_drugs", len(all_drugs))
    for drug in all_drugs:
        sheet_id = drug[0]
        folio_ocamis = drug[1]
        current_uuid = drug[2]
        current_delivered = drug[3]
        if folio_ocamis not in every_folios:
            every_folios[folio_ocamis] = {
                "sheet_ids": {sheet_id},
                "first_uuid": current_uuid,
                "first_delivered": current_delivered,
                "delivered": {current_delivered}
            }
            continue
        current_folio = every_folios[folio_ocamis]
        if sheet_id in current_folio["sheet_ids"]:
            continue
        if current_uuid == current_folio["first_uuid"]:
            continue
        current_tuple = (current_uuid, current_folio["first_uuid"])
        current_folio["delivered"].add(current_delivered)
        for_edit_folios.add(current_tuple)
        current_folio["sheet_ids"].add(sheet_id)
        if len(current_folio["delivered"]) > 1:
            delivered, err = calculate_delivered_final(
                current_folio["delivered"])
            if delivered != current_folio["first_delivered"]:
                current_folio["first_delivered"] = delivered
                current_tuple = (current_folio["first_uuid"], delivered)
                for_edit_delivered.add(current_tuple)
        every_folios[folio_ocamis] = current_folio
    cursor.close()
    return for_edit_folios, for_edit_delivered


def update_folios(for_edit_folios):
    print("start update_folios", datetime.now())
    cursor = connection.cursor()
    sql_delete_temp = "DROP TABLE if exists temp_new_folios"
    cursor.execute(sql_delete_temp)
    create_temp_table = """
        CREATE TEMPORARY TABLE temp_new_folios (
            original_uuid UUID PRIMARY KEY,
            new_uuid UUID
        )
    """
    # SPACE
    folios = ", ".join([f"('{original}', '{new}')"
                        for original, new in for_edit_folios])
    cursor.execute(create_temp_table)
    sql_insert = f"""
        INSERT INTO temp_new_folios (original_uuid, new_uuid)
        VALUES {folios}
    """
    cursor.execute(sql_insert)
    # SPACE
    sql_join = """
        UPDATE formula_drug
        SET prescription_id = temp.new_uuid
        FROM temp_new_folios temp        
        WHERE formula_drug.prescription_id = temp.original_uuid
    """
    cursor.execute(sql_join)
    cursor.execute(sql_delete_temp)
    cursor.close()


def delete_folios(for_edit_folios):
    print("start delete_folios", datetime.now())
    cursor = connection.cursor()
    folios_to_delete = ", ".join([f"'{original}'" for original, new in for_edit_folios])
    sql_delete = f"""
        DELETE FROM formula_prescription pres
        WHERE pres.uuid_folio IN ({folios_to_delete})
    """
    cursor.execute(sql_delete)
    cursor.close()


def update_delivered(for_edit_delivered):
    print("start update_delivered", datetime.now())
    cursor = connection.cursor()
    sql_delete_temp = "DROP TABLE if exists temp_new_delivered"
    cursor.execute(sql_delete_temp)
    create_temp_table = """
        CREATE TEMPORARY TABLE temp_new_delivered (
            original_uuid UUID PRIMARY KEY,
            new_delivered VARCHAR(32)
        )
    """
    # SPACE
    # delivered = ", ".join([f"('{original}', '{new}')" for original, new in for_edit_delivered])
    delivered = [f"('{original}', '{new}')" for original, new in for_edit_delivered]
    delivered = ", ".join(delivered)
    # SPACE
    cursor.execute(create_temp_table)
    sql_insert = f"""
        INSERT INTO temp_new_delivered (original_uuid, new_delivered)
        VALUES 
            {delivered}
    """
    cursor.execute(sql_insert)
    # SPACE
    # sql_get_temp = """
    #     SELECT * FROM temp_new_delivered
    # """
    # cursor.execute(sql_get_temp)
    # temp = cursor.fetchall()
    # print("temp", temp)
    # SPACE
    sql_join = """
        UPDATE formula_prescription
        SET 
            delivered_final_id = temp_new_delivered.new_delivered
        FROM temp_new_delivered
        WHERE formula_prescription.uuid_folio = temp_new_delivered.original_uuid
    """
    cursor.execute(sql_join)
    cursor.execute(sql_delete_temp)
    cursor.close()


def update_sheets_to_merged(filters):
    print("start update_sheets_to_merged", datetime.now())
    cursor = connection.cursor()
    year = filters["year"]
    month = filters["month"]
    year_month = f"{year}-{str(month).zfill(2)}"
    entity_id = filters["entity_id"]
    sql_update = f"""
        UPDATE inai_sheetfile sheet_file
        SET 
            behavior_id = 'merged'
        FROM
            inai_datafile data_file
        WHERE 
            sheet_file.data_file_id = data_file.id AND
            data_file.entity_id = {entity_id} AND
            sheet_file.behavior_id = 'need_merge' OR behavior_id = 'merged' AND
            sheet_file.year_month = '{year_month}'
    """
    cursor.execute(sql_update)
    cursor.close()


def update_and_delete_folios(filters):
    for_edit_folios, for_edit_delivered = get_uuids_duplicates(filters)
    print("start update_and_delete_folios", datetime.now())
    print("for_edit_delivered", len(for_edit_delivered))
    print("folios_to_delete", len(for_edit_folios))
    if len(for_edit_delivered) > 0:
        update_delivered(for_edit_delivered)
    if len(for_edit_folios) > 0:
        update_folios(for_edit_folios)
        delete_folios(for_edit_folios)
    update_sheets_to_merged(filters)


def get_duplicates_folios(filters, is_explore=True):
    from datetime import timedelta
    year = filters["year"]
    month = filters["month"]
    next_month = 1 if month == 12 else month + 1
    next_year = year + 1 if month == 12 else year
    start_date = datetime.strptime(f"{year}-{month}-01", "%Y-%m-%d")
    end_date = datetime.strptime(f"{next_year}-{next_month}-01", "%Y-%m-%d")
    end_date -= timedelta(days=1)
    start_week = start_date.isocalendar()[1]
    start_year = start_date.isocalendar()[0]
    end_week = end_date.isocalendar()[1]
    end_year = end_date.isocalendar()[0]
    all_years = list(range(start_year, end_year + 1))
    print(">>>>>>>>>>>>>>>>>>>>>")
    print("all_years", all_years)
    one_year = len(all_years) == 1
    print(">>>>>>>>>>>>>>>>>>>>>")
    all_pairs = {}
    final_pairs = {"dupli": {}, "shared": {}}
    all_sheets = {}
    unique_counts = {"dupli": 0, "shared": 0, "total": 0}
    # SPACE
    def process_week_explore(final_filters):
        pairs, sheets_totals, month_totals = build_pairs_sheets(final_filters)
        print("start process_week_explore", datetime.now())
        # SPACE
        def add_to_dict(group_name):
            for pair, value in pairs[group_name].items():
                if pair not in final_pairs[group_name]:
                    final_pairs[group_name][pair] = value
                else:
                    final_pairs[group_name][pair] += value
        for group in group_names:
            add_to_dict(group)
            unique_counts[group] += month_totals[group]
        unique_counts["total"] += month_totals["total"]
        # SPACE
        for sheet_id, sheet_value in sheets_totals.items():
            if sheet_id not in all_sheets:
                all_sheets[sheet_id] = sheet_value
            else:
                all_sheets[sheet_id]["total"] += sheet_value["total"]
                all_sheets[sheet_id]["dupli"] += sheet_value["dupli"]
                all_sheets[sheet_id]["shared"] += sheet_value["shared"]
    # SPACE
    for year in all_years:
        filters["year"] = year
        if one_year:
            every_week = list(range(start_week, end_week + 1))
        else:
            if year == start_year:
                every_week = list(range(start_week, 53))
            elif year == end_year:
                every_week = list(range(1, end_week + 1))
            else:
                every_week = list(range(1, 53))
        print("year", year)
        print("every_week", every_week)
        for week in every_week:
            print("...        ...")
            print("week", week)
            filters["week"] = week
            # final_result, sheets = get_duplicates_week(filters)
            print("start_process", datetime.now())
            if is_explore:
                process_week_explore(filters)
            else:
                update_and_delete_folios(filters)
            print("end_process", datetime.now())
    return final_pairs, all_sheets, unique_counts
    # return final_result, sheets


def get_period_report(
        entity_id, is_explore=True, start_month_year=None, end_month_year=None):
    if not start_month_year:
        start_month_year = "201701"
    if not end_month_year:
        today = datetime.today()
        end_month_year = f"{today.month}{today.year}"
    start_year = int(start_month_year[:4])
    start_month = int(start_month_year[-2:])
    end_year = int(end_month_year[:4])
    end_month = int(end_month_year[-2:])
    print("START_PROCESS", datetime.now())
    for year in range(start_year, end_year + 1):
        print("---------------------")
        print("YEAR", year)
        print("---------------------")
        for month in range(1, 13):
            print("++++++++++++++++++")
            print("MONTH", month)
            print("++++++++++++++++++")
            if year == start_year and month < start_month:
                continue
            if year == end_year and month > end_month:
                continue
            filters = {
                "month": month,
                "year": year,
                "entity_id": entity_id,
            }
            result = get_duplicates_folios(filters, is_explore)
            month_pairs, month_sheets, unique_counts = result
            if is_explore:
                save_sheets_months(filters, unique_counts)
                save_crossing_sheets(
                    filters, entity_id, month_pairs, month_sheets)
    print("END_PROCESS", datetime.now())


# my_filter = (53, 20, 2020)
# my_filter = {"month": 5, "year": 2020, "entity_id": 53}
# get_duplicates_folios(my_filter)


# get_period_report(53, True, "201710", "202202")
# get_period_report(53, True, "201711", "201801")
# get_period_report(53, True, "202004", "202006")
# get_period_report(53, False, "201711", "201801")
# get_period_report(53, False, "202004", "202006")
get_period_report(53, True, "201906", "201909")
