from task.aws.common import send_simple_response, BotoUtils

group_names = ["dupli", "shared"]


def get_pairs(input_list):
    from itertools import combinations
    return list(combinations(input_list, 2))


# def analyze_uniques(event, context):
def lambda_handler(event, context):
    # print("model_name", event.get("model_name"))
    drugs = GetDrugs(event)
    all_drugs = drugs()
    uniques_aws = UniquesAws(event, drugs.some_med_column_failed)
    final_result = uniques_aws.build_analysis(all_drugs)

    return send_simple_response(event, context, result=final_result)


class GetDrugs:

    def __init__(self, event: dict):
        self.table_files = event.get("table_files", [])
        self.s3_utils = BotoUtils(event.get("s3"))
        self.some_med_column_failed = False
        self.basic_fields = ["folio_ocamis", "sheet_file_id", "uuid_folio"]
        self.positions = {}

    def __call__(self):

        all_drugs = []
        for table_file in self.table_files:
            csv_content = self.s3_utils.get_object_file(table_file)
            # not_med_column = False
            for idx, cols in enumerate(csv_content):
                if not idx:
                    self.get_positions(cols)
                    continue
                uuid_and_sheet = tuple()
                medicament_key = None
                folio_ocamis = cols[self.positions.get(self.basic_fields[0])]
                # uuid_and_sheet = (cols[self.positions.get("sheet_file_id")],
                #                 cols[self.positions.get("uuid_folio")])
                for field in self.basic_fields[1:]:
                    uuid_and_sheet += (cols[self.positions.get(field)],)
                if not self.some_med_column_failed:
                    medicament_key = cols[self.positions.get("medicament_key")]
                # current_key = (folio_ocamis, medicament_key)
                all_drugs.append((folio_ocamis, medicament_key, uuid_and_sheet))
        return all_drugs

    def get_positions(self, cols):
        if not self.positions:
            for field in self.basic_fields:
                self.positions[field] = cols.index(field)
        if not self.some_med_column_failed:
            try:
                self.positions["medicament_key"] = cols.index("medicament_key")
            except ValueError:
                self.some_med_column_failed = True


class UniquesAws:

    def __init__(self, event: dict, some_med_column_failed: bool):

        self.provider_id = event.get("provider_id")

        self.some_med_column_failed = some_med_column_failed

        field_count = group_names + ["rx_count", "drugs_count"]
        self.counts: dict[str, int] = {field: 0 for field in field_count}
        self.month_sheets = {}

        self.every_folios = {}
        self.month_pairs = {group: {} for group in group_names}
        self.special_group_folios = {group: {} for group in group_names}

    def build_analysis(self, all_drugs):
        self.build_every_folios(all_drugs)
        len_folios = len(self.every_folios)
        if len_folios or self.counts["drugs_count"]:
            print("every_folios", len_folios)
            print("drugs_count", self.counts["drugs_count"])

        self.build_pairs_sheets()
        # self.save_sheets_months(counts)
        # self.save_crossing_sheets(month_pairs, month_sheets)
        result = {
            "month_week_counts": self.counts,
            "month_pairs": self.month_pairs,
            "month_sheets": self.month_sheets
        }
        return result

    def build_every_folios(self, all_drugs):
        for (folio_ocamis, medicament_key, uuid_and_sheet) in all_drugs:
            # medicine_key = None
            # folio_ocamis, sheet_file_id, uuid_folio = drug
            if self.some_med_column_failed:
                medicament_key = None
            self.counts["drugs_count"] += 1
            self.every_folios.setdefault(folio_ocamis, {})
            self.every_folios[folio_ocamis].setdefault(medicament_key, set())
            self.every_folios[folio_ocamis][medicament_key].add(uuid_and_sheet)

    def build_pairs_sheets(self):
        self.get_special_group_folios()

        for group_name in group_names:
            input_dict = self.special_group_folios[group_name]
            for sheet_ids in input_dict.values():
                sheet_ids = sorted(sheet_ids)
                current_pairs = get_pairs(sheet_ids)
                current_pairs = [f"{elem1}|{elem2}"
                                 for elem1, elem2 in current_pairs]
                for pair in current_pairs:
                    self.month_pairs[group_name].setdefault(pair, 0)
                    self.month_pairs[group_name][pair] += 1

    def get_special_group_folios(self):
        for folio_ocamis, medicines in self.every_folios.items():
            self.counts["rx_count"] += 1
            current_folios_uuid = set()
            unique_medicines = set()
            some_dupli = False
            all_sheets = set()

            for medicament_key, values in medicines.items():
                unique_medicines.add(medicament_key)
                unique_sheets = set()
                for sheet_id, uuid_folio in values:
                    current_folios_uuid.add(uuid_folio)
                    all_sheets.add(sheet_id)
                    unique_sheets.add(sheet_id)
                if len(unique_sheets) > 1:
                    some_dupli = True

            group_name = None
            if some_dupli:
                group_name = "dupli"
            elif len(all_sheets) > 1:
                group_name = "shared"

            if group_name:
                self.special_group_folios[group_name][folio_ocamis] = all_sheets
                self.counts[group_name] += 1

            for sheet_id in all_sheets:
                self.month_sheets.setdefault(sheet_id, {
                    "rx_count": 0,
                    "dupli": 0,
                    "shared": 0
                })
                self.month_sheets[sheet_id]["rx_count"] += 1
                if group_name:
                    self.month_sheets[sheet_id][group_name] += 1
