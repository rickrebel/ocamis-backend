from django.db import connection


def get_all_folios(filters):
    cursor = connection.cursor()
    (entity_id, week, year) = filters
    sql_query = f"""
        SELECT
            drug.sheet_file_id AS sheet_id,
            pres.folio_ocamis as folio_ocamis
        FROM
            formula_prescription pres
            INNER JOIN formula_drug drug ON pres.uuid_folio = drug.prescription_id
        WHERE 
            pres.entity_id = {entity_id} AND
            pres.iso_week = {week} AND
            pres.iso_year = {year} 
    """
    cursor.execute(sql_query)
    every_folios = {}
    all_drugs = cursor.fetchall()
    print("all_drugs", len(all_drugs))
    for drug in all_drugs:
        sheet_id = drug[0]
        folio_ocamis = drug[1]
        if folio_ocamis not in every_folios:
            every_folios[folio_ocamis] = {sheet_id}
        else:
            every_folios[folio_ocamis].add(sheet_id)
    print("every_folios", len(every_folios))
    return every_folios


def get_only_duplicate_folios(filters):
    all_folios = get_all_folios(filters)
    only_duplicate_folios = {}
    totals_by_sheet = {}
    for folio, sheet_ids in all_folios.items():
        sheets_count = len(sheet_ids)
        for sheet_id in sheet_ids:
            if sheet_id not in totals_by_sheet:
                totals_by_sheet[sheet_id] = {"total": 1, "duplicates": 0}
            else:
                totals_by_sheet[sheet_id]["total"] += 1
        if sheets_count > 1:
            only_duplicate_folios[folio] = sheet_ids
            for sheet_id in sheet_ids:
                totals_by_sheet[sheet_id]["duplicates"] += 1
    return only_duplicate_folios, totals_by_sheet


def get_pairs(input_list):
    from itertools import combinations
    return list(combinations(input_list, 2))


def build_pairs_sheets(filters):
    dupli, sheets = get_only_duplicate_folios(filters)
    print("dupli", len(dupli))
    every_pairs = {}
    for folio, sheet_ids in dupli.items():
        # sort the sheet_ids:
        sheet_ids = sorted(sheet_ids)
        pairs = get_pairs(sheet_ids)
        for pair in pairs:
            if pair not in every_pairs:
                every_pairs[pair] = 1
            else:
                every_pairs[pair] += 1
    print("every_pairs", len(every_pairs))
    return every_pairs, sheets


def get_duplicates_week(filters):
    # final_pairs, sheets = build_pairs_sheets(53, 49, 2017)
    final_pairs, sheets = build_pairs_sheets(filters)

    # for sheet in sheets:
    #     print(sheet, sheets[sheet])
    final_result = []
    for pair in final_pairs.keys():
        (sheet_id_1, sheet_id_2) = pair
        current_pair = final_pairs[pair]
        sheet_1 = sheets[sheet_id_1]
        sheet_2 = sheets[sheet_id_2]
        percent_1 = current_pair / sheet_1["total"]
        percent_2 = current_pair / sheet_2["total"]
        current_result = (
            sheet_id_1, sheet_id_2, sheet_1["total"], sheet_2["total"],
            current_pair, percent_1, percent_2)
        final_result.append(current_result)

    for final in final_result:
        print(final)
    return final_result, sheets


def get_duplicates_folios(filters):
    from datetime import datetime, timedelta
    year = filters["year"]
    month = filters["month"]
    next_month = 1 if month == 12 else month + 1
    next_year = year + 1 if month == 12 else year
    start_date = datetime.strptime(f"{year}-{month}-01", "%Y-%m-%d")
    end_date = datetime.strptime(f"{next_year}-{next_month}-01", "%Y-%m-%d")
    end_date -= timedelta(days=1)
    start_week = start_date.isocalendar()[1]
    end_week = end_date.isocalendar()[1]
    every_week = list(range(start_week, end_week + 1))
    for week in every_week:
        filters["week"] = week
        final_result, sheets = get_duplicates_week(filters)
    # return final_result, sheets


# my_filter = (53, 20, 2020)
my_filter = {"month": 5, "year": 2020, "entity_id": 53}
get_duplicates_folios(my_filter)
