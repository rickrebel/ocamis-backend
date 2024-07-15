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


class UniquesAws:

    def __init__(self, event: dict, context):

        self.provider_id = event.get("provider_id")
        self.table_files = event.get("table_files", [])
        self.has_medicine_key = event.get("has_medicine_key", False)
        self.med_column_failed = not self.has_medicine_key

        self.s3_utils = BotoUtils(event.get("s3"))
        self.unique_counts = {
            "dupli": 0, "shared": 0, "rx_count": 0, "drugs_count": 0}
        self.month_sheets = {}
        self.positions = {}

        self.context = context

    def build_analysis(self):
        all_folios = self.get_all_drugs()
        len_folios = len(all_folios)
        if len_folios or self.unique_counts["drugs_count"]:
            print("every_folios", len_folios)
            print("drugs_count", self.unique_counts["drugs_count"])

        month_pairs = self.build_pairs_sheets(all_folios)
        # self.save_sheets_months(unique_counts)
        # self.save_crossing_sheets(month_pairs, month_sheets)
        result = {
            "month_week_counts": self.unique_counts,
            "month_pairs": month_pairs,
            "month_sheets": self.month_sheets
        }
        return result

    def get_positions(self, cols, basic_fields):
        if not self.positions:
            for field in basic_fields:
                self.positions[field] = cols.index(field)
        if not self.med_column_failed:
            try:
                self.positions["medicament_key"] = cols.index("medicament_key")
            except ValueError:
                self.med_column_failed = True

    def get_all_drugs(self):

        # basic_fields = ["folio_ocamis", "sheet_file_id", "uuid_folio", "month"]
        basic_fields = ["folio_ocamis", "sheet_file_id", "uuid_folio"]
        all_drugs = []
        for table_file in self.table_files:
            csv_content = self.s3_utils.get_object_file(table_file)
            # not_med_column = False
            for idx, cols in enumerate(csv_content):
                if not idx:
                    self.get_positions(cols, basic_fields)
                    continue
                current_util = tuple()
                folio_ocamis = None
                medicament_key = None
                for field in basic_fields:
                    if field == "folio_ocamis":
                        folio_ocamis = cols[self.positions.get(field)]
                    else:
                        current_util += (cols[self.positions.get(field)],)
                if not self.med_column_failed:
                    medicament_key = cols[self.positions.get("medicament_key")]

                # current_key = (folio_ocamis, medicament_key)
                all_drugs.append((folio_ocamis, medicament_key, current_util))
        every_folios = {}
        for drug in all_drugs:
            # medicine_key = None

            # folio_ocamis, sheet_file_id, uuid_folio = drug
            folio_ocamis, medicament_key, uuid_and_sheet = drug
            if self.med_column_failed:
                medicament_key = None
            # folio_ocamis, medicament_key = folio_key

            # if month == self.current_month:
            #     drugs_count += 1
            self.unique_counts["drugs_count"] += 1
            # uuid_and_sheet = (sheet_file_id, uuid_folio, month)
            # uuid_and_sheet = (sheet_file_id, uuid_folio)
            every_folios.setdefault(folio_ocamis, {})
            every_folios[folio_ocamis].setdefault(medicament_key, set())
            every_folios[folio_ocamis][medicament_key].add(uuid_and_sheet)
            # if folio_ocamis not in every_folios:
            #     every_folios[folio_ocamis] = {uuid_and_sheet}
            # else:
            #     every_folios[folio_ocamis].add(uuid_and_sheet)
        return every_folios

    def build_pairs_sheets(self, all_folios):
        folios = self.get_duplicate_folios(all_folios)

        def build_small_pairs(input_dict, input_name):
            # len_input = len(input_dict)
            # if len_input:
            #     print(input_name, len_input)
            every_pairs = {}
            for sheet_ids in input_dict.values():
                sheet_ids = sorted(sheet_ids)
                current_pairs = get_pairs(sheet_ids)
                current_pairs = [f"{elem1}|{elem2}" for elem1, elem2 in current_pairs]
                for pair in current_pairs:
                    every_pairs.setdefault(pair, 0)
                    every_pairs[pair] += 1
            # len_pairs = len(every_pairs)
            # if len_pairs:
            #     print(input_name, len_pairs)
            return every_pairs

        pairs = {}
        for group_name in group_names:
            pairs[group_name] = build_small_pairs(folios[group_name], group_name)
        return pairs

    def get_duplicate_folios(self, all_folios):
        folios = {"dupli": {}, "shared": {}}
        # for folio in all_folios.keys():
        # print("all_folios", all_folios)
        for folio_ocamis, medicines in all_folios.items():
            self.unique_counts["rx_count"] += 1
            current_folios_uuid = set()
            unique_medicines = set()
            # "sheet_file_id", "uuid_folio", "month"
            # for sheet_id, uuid_folio, month in values:
            some_dupli = False
            all_sheets = set()

            for medicament_key, values in medicines.items():
                unique_medicines.add(medicament_key)
                current_sheets = set()
                for sheet_id, uuid_folio in values:
                    current_folios_uuid.add(uuid_folio)
                    all_sheets.add(sheet_id)
                    current_sheets.add(sheet_id)
                len_sheets = len(current_sheets)
                if len_sheets > 1:
                    some_dupli = True

            group_name = None
            if some_dupli:
                group_name = "dupli"
            elif len(all_sheets) > 1:
                group_name = "shared"

            if group_name:
                folios[group_name][folio_ocamis] = all_sheets
                self.unique_counts[group_name] += 1

            for sheet_id in all_sheets:
                self.month_sheets.setdefault(sheet_id, {
                    "rx_count": 0,
                    "dupli": 0,
                    "shared": 0
                })
                self.month_sheets[sheet_id]["rx_count"] += 1
                if group_name == "dupli":
                    self.month_sheets[sheet_id]["dupli"] += 1
                elif group_name == "shared":
                    self.month_sheets[sheet_id]["shared"] += 1

        return folios
