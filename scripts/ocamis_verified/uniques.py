from django.db import connection
from task.aws.common import calculate_delivered_final
from datetime import datetime
from inai.models import SheetFile

group_names = ["dupli", "shared"]


def get_all_folios(filters):
    cursor = connection.cursor()
    entity_id = filters["entity_id"]
    year = filters["year"]
    week = filters["week"]
    excluded_sheets = filters.get("excluded_sheets", set())
    sql_query = f"""
        SELECT
            sheet_id,
            uuid_folio,
            folio_ocamis,
            month
        FROM
            drugs_and_rxs
        WHERE
            entity_id = {entity_id} AND
            iso_week = {week} AND
            iso_year = {year}
    """
    cursor.execute(sql_query)
    every_folios = {}
    all_drugs = cursor.fetchall()
    len_drugs = len(all_drugs)
    print("end of query get", datetime.now())
    if len_drugs:
        print("all_drugs (explore):", len_drugs)
    # for idx in range(len_drugs):
    for drug in all_drugs:
        # drug = all_drugs.pop()
        sheet_id, uuid_folio, folio_ocamis, month = drug
        if sheet_id in excluded_sheets:
            continue
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


def save_sheets_months(year_month, entity_id, month_counts):
    from inai.models import EntityMonth
    current_entity_months = EntityMonth.objects.filter(
        entity_id=entity_id, year_month=year_month)
    current_entity_months.update(
        duplicates_count=month_counts["dupli"],
        shared_count=month_counts["shared"],
        rx_count=month_counts["total"]
    )


# def save_crossing_sheets(entity_id, dupli_pairs, shared_pairs, sheets):
def save_crossing_sheets(year_month, entity_id, month_pairs, sheets):
    from django.utils import timezone
    from inai.models import CrossingSheet
    print("start save_crossing_sheets", timezone.now())
    # SPACE
    shared_pairs = month_pairs["shared"]
    edited_crosses = []
    # SPACE
    for sheet_id, value in sheets.items():
        current_sheet = SheetFile.objects.get(id=sheet_id)
        if current_sheet.year_month != year_month:
            continue
        current_sheet.rx_count = value["total"]
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
        # if not created:
        #     print("cross", cross)
        #     print("last_crossing", cross.last_crossing)
        #     print("!!!!!!!!!!!!!!!!!!!!!\n")
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


def get_delivered_results(filters):
    print("start get_delivered_results", datetime.now())
    cursor = connection.cursor()
    entity_id = filters["entity_id"]
    month = filters["month"]
    week = filters["week"]
    year = filters["year"]
    excluded_sheets = filters.get("excluded_sheets", set())
    month_str = str(month).zfill(2)
    year_month = f"{year}-{month_str}"
    # SPACE
    sql_query = f"""
        SELECT
            sheet_id,
            folio_ocamis,
            uuid_folio,
            delivered,
            month
        FROM
            drugs_and_rxs
        WHERE 
            entity_id = {entity_id} AND
            iso_week = {week} AND
            iso_year = {year}
    """
    cursor.execute(sql_query)
    every_folios = {}
    all_drugs = cursor.fetchall()
    len_all_drugs = len(all_drugs)
    if len_all_drugs:
        print("all_drugs (result)", len(all_drugs))
    valid_delivered = ["partial", "denied", "zero", "complete"]
    for drug in all_drugs:
        sheet_id, folio_ocamis, current_uuid, current_delivered, curr_month = drug
        if "None" in current_delivered:
            for delivered_text in valid_delivered:
                if delivered_text in current_delivered:
                    current_delivered = delivered_text
                    break
        if sheet_id in excluded_sheets:
            continue
        if curr_month != month:
            continue
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
        current_folio["delivered"].add(current_delivered)
        current_folio["sheet_ids"].add(sheet_id)
        if len(current_folio["delivered"]) > 1:
            delivered, err = calculate_delivered_final(
                current_folio["delivered"])
            if delivered != current_folio["first_delivered"]:
                current_folio["first_delivered"] = delivered
        every_folios[folio_ocamis] = current_folio
    cursor.close()
    results = {}
    for folio_ocamis, values in every_folios.items():
        delivered = values["first_delivered"]
        if delivered not in results:
            results[delivered] = 1
        else:
            results[delivered] += 1
    return results


def get_uuids_duplicates(filters):
    print("start get_uuids_duplicates", datetime.now())
    cursor = connection.cursor()
    entity_id = filters["entity_id"]
    week = filters["week"]
    month = filters["month"]
    year = filters["year"]
    excluded_sheets = filters.get("excluded_sheets", set())
    month_str = str(month).zfill(2)
    # year_month = f"{year}-{month_str}"
    # SPACE
    sql_query = f"""
        SELECT
            sheet_id,
            folio_ocamis,
            uuid_folio,
            delivered
        FROM
            drugs_and_rxs        
        WHERE 
            entity_id = {entity_id} AND
            iso_week = {week} AND
            iso_year = {year}
    """
    cursor.execute(sql_query)
    every_folios = {}
    for_edit_folios = set()
    for_edit_delivered = set()
    all_drugs = cursor.fetchall()
    len_all_drugs = len(all_drugs)
    if len_all_drugs:
        print("all_drugs (trans)", len(all_drugs))
    for drug in all_drugs:
        sheet_id, folio_ocamis, current_uuid, current_delivered = drug
        if sheet_id in excluded_sheets:
            continue
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
    print("folios", len(for_edit_folios))
    cursor.execute(create_temp_table)
    sql_insert = f"""
        INSERT INTO temp_new_folios (original_uuid, new_uuid)
        VALUES {folios}
    """
    cursor.execute(sql_insert)
    # SPACE
    sql_join = """
        UPDATE formula_drug
        SET rx_id = temp.new_uuid
        FROM temp_new_folios temp
        WHERE formula_drug.rx_id = temp.original_uuid
    """
    cursor.execute(sql_join)
    cursor.execute(sql_delete_temp)
    cursor.close()


def delete_folios(for_edit_folios):
    print("start delete_folios", datetime.now())
    cursor = connection.cursor()
    folios_to_delete = ", ".join([f"'{original}'" for original, new in for_edit_folios])
    sql_delete = f"""
        DELETE FROM formula_rx rx
        WHERE rx.uuid_folio IN ({folios_to_delete})
    """
    result = cursor.execute(sql_delete)
    print("result", result)
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
    all_delivered = {original: new for original, new in for_edit_delivered}
    delivered = [f"('{original}', '{new}')"
                 for original, new in all_delivered.items()]
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
        UPDATE formula_rx
        SET 
            delivered_final_id = temp_new_delivered.new_delivered
        FROM temp_new_delivered
        WHERE formula_rx.uuid_folio = temp_new_delivered.original_uuid
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
    batch_size = 100000
    while True:
        if len(for_edit_folios) == 0:
            break
        current_batch = batch_size \
            if len(for_edit_folios) > batch_size else len(for_edit_folios)
        current_folios = []
        for i in range(current_batch):
            current_folios.append(for_edit_folios.pop())
        update_folios(current_folios)
        delete_folios(current_folios)
    # if len(for_edit_folios) > 0:
    #     update_folios(for_edit_folios)
    #     delete_folios(for_edit_folios)
    update_sheets_to_merged(filters)


def get_duplicates_folios(filters, is_explore):
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
    final_pairs = {"dupli": {}, "shared": {}}
    all_sheets = {}
    result_delivered = {}
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
            if is_explore == 'result':
                week_result = get_delivered_results(filters)
                for delivered, value in week_result.items():
                    if delivered not in result_delivered:
                        result_delivered[delivered] = value
                    else:
                        result_delivered[delivered] += value
            elif is_explore:
                process_week_explore(filters)
            else:
                update_and_delete_folios(filters)
            print("end_process", datetime.now())
    if is_explore == 'result':
        return None, None, result_delivered
    return final_pairs, all_sheets, unique_counts
    # return final_result, sheets


def refresh_materialized_views():
    cursor = connection.cursor()
    sql_queries = [
        # "alter table public.formula_rx"
        # "    add constraint formula_rx_pkey"
        # "    primary key(uuid_folio);",
        # "alter table formula_drug"
        # "    add constraint formula_drug_rx_id_cdf044b3_fk_formula_p"
        # "    foreign key(rx_id) references formula_rx"
        # "    deferrable initially deferred;",
        # "create index if not exists formula_drug_rx_id_cdf044b3"
        # "    on formula_drug(rx_id);",
        "CREATE INDEX if not exists d_and_p_entity_id_iso_week_iso_year"
        "    ON drugs_and_rxs(entity_id, iso_week, iso_year);",
        # "CREATE INDEX if not exists d_and_p_entity_id_month_iso_year"
        # "    ON drugs_and_rxs(entity_id, month, iso_year);",
        "REFRESH MATERIALIZED VIEW drugs_and_rxs WITH DATA;",
        # "DROP INDEX if exists d_and_p_entity_id_iso_week_iso_year;",
    ]
    for sql in sql_queries:
        print("PRE: ", datetime.now())
        print(">> ", sql)
        try:
            cursor.execute(sql)
        except Exception as e:
            print("ERROR!!!:\n", e)
    print("PRE: ", datetime.now())
    cursor.close()


def delete_indexes_and_constraints():
    cursor = connection.cursor()
    sql_queries = [
        "drop index if exists formula_drug_rx_id_cdf044b3",
        "alter table formula_drug"
        "    drop constraint formula_drug_rx_id_cdf044b3_fk_formula_p",
        "alter table public.formula_rx"
        "    drop constraint formula_rx_pkey",
    ]
    for sql in sql_queries:
        try:
            cursor.execute(sql)
        except Exception as e:
            print("e", e)
    cursor.close()


def get_period_report(
        entity_id, is_explore='True', start_month_year=None,
        end_month_year=None, refresh=False):
    if not start_month_year:
        start_month_year = "2017-01"
    if not end_month_year:
        today = datetime.today()
        end_month_year = f"{today.month}-{today.year}"
    if refresh:
        refresh_materialized_views()
        # delete_indexes_and_constraints()
    if is_explore:
        behaviors = ["invalid"]
    else:
        behaviors = ["invalid", "pending", "not_merge"]
    excluded_sheets = SheetFile.objects.filter(
        data_file__entity_id=entity_id,behavior_id__in=behaviors)\
        .values_list("id", flat=True)
    excluded_sheets = set(list(excluded_sheets))
    print("excluded_sheets", excluded_sheets)
    start_year, start_month = start_month_year.split("-")
    start_year = int(start_year)
    start_month = int(start_month)
    end_year, end_month = end_month_year.split("-")
    end_year = int(end_year)
    end_month = int(end_month)
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
                "excluded_sheets": excluded_sheets,
            }
            # if is_explore == 'result':
            #     print("Sí estoy en result")
            #     get_delivered_results(filters)
            # else:
            result = get_duplicates_folios(filters, is_explore)
            month_pairs, month_sheets, unique_counts = result
            year_month = f"{year}-{month:02}"
            if is_explore == 'result':
                for delivered, value in unique_counts.items():
                    print("|", year_month, "|", delivered, "|", value, "|")
                print("Sí estoy en result")
            elif is_explore:
                save_sheets_months(year_month, entity_id, unique_counts)
                save_crossing_sheets(
                    year_month, entity_id, month_pairs, month_sheets)
    print("END_PROCESS", datetime.now())


# my_filter = (53, 20, 2020)
# my_filter = {"month": 5, "year": 2020, "entity_id": 53}
# get_duplicates_folios(my_filter)


# get_period_report(53, True, "201710", "202202")
# get_period_report(53, True, "201711", "201801")
# get_period_report(53, True, "202004", "202006")
# get_period_report(53, False, "201711", "201801")
# get_period_report(53, False, "202004", "202006")
# get_period_report(53, True, "201809", "201901")
# get_period_report(53, True, "201811", "202302", refresh=False)
# explore = ""
# get_period_report(53, explore, "2017-01", "2020-10", refresh=False)

def improvisado():
    explore_result = 'result'
    # get_period_report(53, explore_result, "2017-01", "2020-11", refresh=False)
    # get_period_report(53, explore_result, "2019-07", "2023-04", refresh=False)
    get_period_report(53, explore_result, "2017-12", "2017-12", refresh=False)
    get_period_report(53, explore_result, "2018-11", "2018-11", refresh=False)
    get_period_report(53, explore_result, "2019-01", "2019-01", refresh=False)
    get_period_report(53, explore_result, "2019-07", "2019-09", refresh=False)
    get_period_report(53, explore_result, "2020-05", "2020-05", refresh=False)


# get_period_report(53, "result", "2017-01", "2017-01", refresh=False)

# get_period_report(53, False, "201701", "201701", refresh=False)

# create index if not exists formula_rx_pkey_temp
#      on formula_rx(uuid_folio);

# create index if not exists formula_drug_rx_id_cdf044b3
#          on formula_drug(rx_id);

# create index if not exists d_and_p_sheet_id
#          on drugs_and_rxs(sheet_id);

# create index if not exists formula_drug_sheet_file_id_568cdddf
#     on formula_drug (sheet_file_id);
