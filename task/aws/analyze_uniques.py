from task.aws.common import send_simple_response, BotoUtils

group_names = ["dupli", "shared"]


def get_pairs(input_list):
    from itertools import combinations
    return list(combinations(input_list, 2))


# def analyze_uniques(event, context):
def lambda_handler(event, context):
    # print("model_name", event.get("model_name"))
    uniques_aws = UniquesAws(event, context)
    final_result = uniques_aws.build_analysis()
    return send_simple_response(event, context, result=final_result)


def get_duplicate_folios(all_folios):
    totals_by_sheet = {}
    month_week_counts = {"dupli": 0, "shared": 0, "rx_count": 0}
    folios = {"dupli": {}, "shared": {}}
    # for folio in all_folios.keys():
    # print("all_folios", all_folios)
    for folio_ocamis, values in all_folios.items():
        # values = all_folios.pop(folio)
        # sheets_count = len(values)
        # sheets_count = 0
        # is_same_month = False
        current_sheets = set()
        current_uuid = set()
        # "sheet_file_id", "uuid_folio", "month"
        # for sheet_id, uuid_folio, month in values:
        for sheet_id, uuid_folio in values:
            current_sheets.add(sheet_id)
            current_uuid.add(uuid_folio)
            # if not is_same_month:
            #     is_same_month = self.current_month == int(month)
            #     is_same_month = self.current_month == int(month)
        # if is_same_month:
        #     month_week_counts["rx_count"] += 1
        month_week_counts["rx_count"] += 1
        len_uuids = len(current_uuid)
        len_sheets = len(current_sheets)
        if len_sheets > 1:
            group_name = "shared" if len_uuids == 1 else "dupli"
            folios[group_name][folio_ocamis] = current_sheets
            # if is_same_month:
            #     month_week_counts[group_name] += 1
            month_week_counts[group_name] += 1
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
                    "rx_count": 1,
                    "dupli": duplicates_plus,
                    "shared": shared_plus}
            else:
                totals_by_sheet[sheet_id]["rx_count"] += 1
                totals_by_sheet[sheet_id]["shared"] += shared_plus
                totals_by_sheet[sheet_id]["dupli"] += duplicates_plus
    return folios, totals_by_sheet, month_week_counts


def build_pairs_sheets(all_folios):
    folios, sheets, month_week_counts = get_duplicate_folios(all_folios)

    def build_small_pairs(input_dict, input_name):
        len_input = len(input_dict)
        if len_input:
            print(input_name, len_input)
        every_pairs = {}
        for folio, sheet_ids in input_dict.items():
            sheet_ids = sorted(sheet_ids)
            current_pairs = get_pairs(sheet_ids)
            current_pairs = [f"{elem1}|{elem2}" for elem1, elem2 in current_pairs]
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
    return pairs, sheets, month_week_counts


class UniquesAws:

    def __init__(self, event: dict, context):

        self.entity_id = event.get("entity_id")
        self.table_files = event.get("table_files", [])

        self.s3_utils = BotoUtils(event.get("s3"))

        self.context = context

    def build_analysis(self):
        # all_drugs = self.get_all_drugs()
        # all_folios = get_every_folios(all_drugs)
        all_folios, drugs_count = self.get_all_drugs()
        len_folios = len(all_folios)
        if len_folios or drugs_count:
            print("every_folios", len_folios)
            print("drugs_count", drugs_count)
        # pairs, sheets_totals, month_totals = build_pairs_sheets(all_folios)
        result_pairs_sheets = build_pairs_sheets(all_folios)
        # final_pairs, all_sheets, unique_counts = result_pairs_sheets
        month_pairs, month_sheets, unique_counts = result_pairs_sheets
        unique_counts["drugs_count"] = drugs_count
        # self.save_sheets_months(unique_counts)
        # self.save_crossing_sheets(month_pairs, month_sheets)
        result = {
            "month_week_counts": unique_counts,
            "month_pairs": month_pairs,
            "month_sheets": month_sheets,
        }
        return result

    def get_all_drugs(self):

        # basic_fields = ["folio_ocamis", "sheet_file_id", "uuid_folio", "month"]
        basic_fields = ["folio_ocamis", "sheet_file_id", "uuid_folio"]
        positions = {}
        all_drugs = []
        for table_file in self.table_files:
            # file = table_file["file"]
            # csv_content = self.s3_utils.get_object_file(file)
            csv_content = self.s3_utils.get_object_file(table_file)
            # csv_data = csv.reader(io.StringIO(data), delimiter='|')
            for idx, cols in enumerate(csv_content):
                # print("idx", idx)
                # print("row", cols)
                # cols = row.split("|")
                if not idx:
                    if not positions:
                        for field in basic_fields:
                            positions[field] = cols.index(field)
                    continue
                current_util = []
                for field in basic_fields:
                    current_util.append(cols[positions.get(field)])
                all_drugs.append(current_util)
        every_folios = {}
        drugs_count = 0
        for drug in all_drugs:
            # folio_ocamis, sheet_file_id, uuid_folio, month = drug
            folio_ocamis, sheet_file_id, uuid_folio = drug
            # if month == self.current_month:
            #     drugs_count += 1
            drugs_count += 1
            # uuid_and_sheet = (sheet_file_id, uuid_folio, month)
            uuid_and_sheet = (sheet_file_id, uuid_folio)
            if folio_ocamis not in every_folios:
                every_folios[folio_ocamis] = {uuid_and_sheet}
            else:
                every_folios[folio_ocamis].add(uuid_and_sheet)
        return every_folios, drugs_count
