import io
import csv
import uuid as uuid_lib
import json
import unidecode
import re
from task.aws.common import (
    obtain_decode, calculate_delivered_final, send_simple_response, BotoUtils)


def text_normalizer(text):
    text = text.upper().strip()
    text = unidecode.unidecode(text)
    return re.sub(r'[^a-zA-Z\s]', '', text)


# def start_build_csv_data(event, context={"request_id": "test"}):
def lambda_handler(event, context):
    # if "artificial_request_id" in event:
    #     context["aws_request_id"] = event["artificial_request_id"]
    init_data = event["init_data"]
    init_data["s3"] = event["s3"]
    match_aws = MatchAws(init_data, context)

    file = event["file"]

    final_result = match_aws.build_csv_to_data(file)
    return send_simple_response(event, context, result=final_result)


class MatchAws:

    def __init__(self, init_data: dict, context):
        from datetime import datetime
        for key, value in init_data.items():
            setattr(self, key, value)

        self.sheet_file_id = init_data.get("sheet_file_id")
        self.lap_sheet_id = init_data.get("lap_sheet_id")
        self.file_name_simple = init_data["file_name_simple"]
        self.sheet_name = init_data["sheet_name"]
        self.final_path = init_data["final_path"]

        self.entity_id = init_data["entity_id"]
        self.split_by_delegation = init_data["split_by_delegation"]
        self.global_delegation = init_data["global_delegation"]
        self.global_clues = init_data["global_clues"]

        self.decode = init_data["decode"]
        self.decode_final = 'utf-8'
        self.row_start_data = init_data["row_start_data"]
        self.delimiter = init_data["delimiter"]

        self.delimit = self.delimiter or "|"
        self.sep = "\|" if self.delimit == "|" else self.delimit
        self.string_date = init_data["string_date"].strip()
        self.string_dates = [
            date.strip() for date in self.string_date.split(";")]
        self.columns_count = init_data["columns_count"]
        # print("string_date", self.string_date)

        editable_models = init_data["editable_models"]
        self.normal_models = [model for model in editable_models
                              if model["name"] not in ["drug", "rx"]]
        self.real_models = init_data["real_models"]
        self.model_fields = init_data["model_fields"]
        self.hash_null = init_data["hash_null"]
        self.med_cat_models = [cat for cat in editable_models
                               if cat.get("app") == "med_cat"]
        self.real_med_cat_models = [cat["name"] for cat in self.med_cat_models
                                    if cat["model"] in self.real_models]
        self.med_cat_flat_fields = {}
        self.initial_data = {}
        for cat_name in self.real_med_cat_models:
            is_med_unit = cat_name == "medical_unit"
            is_medicament = cat_name == "medicament"
            fields = []
            data_values = []
            all_values = []
            for field in self.model_fields[cat_name]:
                field_name = field["name"]
                if field_name == "hex_hash":
                    continue
                value = None
                field["name"] = field_name
                field["default_value"] = None
                if field["is_relation"]:
                    if field_name == "entity_id" and not is_medicament:
                        value = self.entity_id
                        data_values.append(str(value))
                    if is_med_unit:
                        if field_name == "delegation_id" and self.global_delegation:
                            value = self.global_delegation["id"]
                        elif field_name == "clues_id" and self.global_clues:
                            value = self.global_clues["id"]
                    all_values.append(value)
                elif is_med_unit:
                    if field_name == "clues_key" and self.global_clues:
                        field["default_value"] = self.global_clues["clues_key"]
                    elif field_name == "delegation_name" and self.global_delegation:
                        field["default_value"] = self.global_delegation["name"]
                fields.append(field)
            flat_fields = [field for field in fields if not field["is_relation"]]
            self.med_cat_flat_fields[cat_name] = flat_fields
            self.initial_data[cat_name] = {"data_values": data_values,
                                           "all_values": all_values}
        # print("med_cat_flat_fields: \n", self.med_cat_flat_fields)
        self.delegation_cat = init_data.get("delegation_cat", {})

        self.months = set()
        self.buffers = {}
        self.csvs = {}
        for model in self.normal_models:
            self.csvs[model["name"]] = io.StringIO()
            self.buffers[model["name"]] = csv.writer(
                self.csvs[model["name"]], delimiter="|")

        self.existing_fields = init_data["existing_fields"]
        self.positioned_fields = [field for field in self.existing_fields
                                  if field["position"] is not None]
        self.special_fields = [field for field in self.existing_fields
                               if field["is_special"]]

        # self.sep_fields = [field for field in self.existing_fields
        #                    if field.get("clean_function") == "same_separator"]
        self.sep_fields = [field for field in self.existing_fields
                           if field.get("same_separator")]
        self.copy_from_up = [field for field in self.existing_fields
                             if field.get("same_group_data")]
        amount_fields = [field for field in self.existing_fields
                         if "_amount" in field["name"] or
                         "clasif_assortment" in field["name"]]

        self.global_delivered = None
        if len(amount_fields) == 1:
            amount_field = amount_fields[0]
            if amount_field["name"] == "delivered_amount":
                self.global_delivered = "only_delivered"
            elif amount_field["name"] == "prescribed_amount":
                self.global_delivered = "only_prescribed"

        self.some_same_separator = len(self.sep_fields) > 0
        self.regex_fields = []
        for field in self.existing_fields:
            # separator = field.get("separator")
            regex_string = None
            if field["regex_format"] and len(field["regex_format"]) > 10:
                regex_string = field["regex_format"][1:-1]
                regex_string = f"{self.sep}?({regex_string}){self.sep}?"
            # if field.get("clean_function") == "simple_regex":
            #     regex_string = field["t_value"]
            #     regex_string = f"{self.sep}({regex_string}){self.sep}"
            simple_regex = field.get("simple_regex")
            if simple_regex:
                regex_string = f"{self.sep}({simple_regex}){self.sep}"
            elif field["data_type"] == "Datetime":
                if self.string_date == "MANY":
                    date_regex = field.get("format_date")
                    if ";" in date_regex:
                        pass
                    elif date_regex:
                        regex_string = self.string_time_to_regex(date_regex)
                    else:
                        regex_string = False
                elif self.string_date != "EXCEL" and ";" not in self.string_date:
                    regex_string = self.string_time_to_regex(self.string_date)
            if regex_string:
                field["regex"] = regex_string
                self.regex_fields.append(field)
        if self.regex_fields:
            last_block = {
                "position": self.positioned_fields[-1]["position"] + 1,
                "regex": f"$"
            }
            self.regex_fields += [last_block]

        self.lap = init_data["lap"]
        self.cat_keys = {}
        for med_cat in self.real_med_cat_models:
            self.cat_keys[med_cat] = set()

        self.last_revised = datetime.now()

        self.last_missing_row = None
        self.all_missing_rows = []
        self.all_missing_fields = []

        self.s3_utils = BotoUtils(init_data.get("s3"))

        self.context = context
        self.last_date = None
        self.last_valid_row = None
        self.last_date_formatted = None
        self.is_prepare = init_data.get("is_prepare", False)
        self.example_count = 0

    def build_csv_to_data(self, file):

        file_type = "json" if self.is_prepare else "csv"
        complete_file = self.s3_utils.get_csv_lines(file, file_type)
        if self.is_prepare:
            complete_file = json.loads(complete_file.read())
            data_rows = complete_file.get("all_data", [])
            tail_data = complete_file.get("tail_data", [])
            data_rows.extend(tail_data)
        else:
            data_rows = complete_file.readlines()
            # data_rows = complete_file
        all_data = self.divide_rows(data_rows)
        for cat in self.normal_models:
            self.build_headers(cat["name"])
        for cat_name in self.real_med_cat_models:
            self.generic_match(cat_name, {}, True)
        rx_cats = [cat_name for cat_name in self.real_med_cat_models
                   if cat_name != "medicament"]

        csvs_by_date = {}
        buffers_by_date = {}
        totals_by_date = {}

        special_cols = self.build_special_cols(all_data)
        required_cols = [col for col in self.existing_fields
                         if col["required_row"]]

        # last_date = None
        # iso_date = None
        # first_iso = None
        all_rx = {}
        success_drugs_count = 0
        total_count = len(all_data)
        processed_count = 0
        classify_cols = [col for col in self.existing_fields
                         if col["name"] == "clasif_assortment_presc"]
        classify_id = classify_cols[0]["name_column"] if classify_cols else None

        discarded_count = self.row_start_data - 1

        for row in all_data[self.row_start_data - 1:]:
            required_cols_in_null = [col for col in required_cols
                                     if not row[col["position"]]]
            if required_cols_in_null:
                discarded_count += 1
                continue
            processed_count += 1
            # print("data_row \t", data_row)
            self.last_missing_row = None
            # is_same_date = False
            uuid = str(uuid_lib.uuid4())

            available_data = {
                "entity_id": self.entity_id,
                "sheet_file_id": self.sheet_file_id,
                "lap_sheet_id": self.lap_sheet_id,
                "row_seq": int(row[0]),
                "uuid": uuid,
            }
            available_data = self.special_available_data(
                available_data, row, special_cols)

            available_data, some_date = self.complement_available_data(
                available_data, row)

            if not some_date:
                error = "Fechas; No se pudo convertir ninguna fecha"
                # print("some_date", some_date)
                # print("row", row)
                self.append_missing_row(row, error)
                continue
            # if last_date != date[:10]:
            #     last_date = date[:10]
            try:
                iso_date = some_date.isocalendar()
            except Exception as e:
                # print(some_date)
                error = f"Error en fecha {some_date}; {e}"
                # print(error)
                self.append_missing_row(row, error)
                continue
            iso_year = iso_date[0]
            iso_week = iso_date[1]
            iso_day = iso_date[2]
            year = some_date.year
            month = some_date.month
            iso_delegation, iso_del2, delegation_error = self.delegation_match(
                available_data)
            if delegation_error:
                self.append_missing_row(row, delegation_error)
                continue
            complex_date = (iso_year, iso_week, iso_del2, year, month)
            if complex_date not in buffers_by_date:
                all_rx[complex_date] = {}
                totals_by_date[complex_date] = {
                    "drugs_count": 0, "rx_count": 0}
                csvs_by_date[complex_date] = io.StringIO()
                buffers_by_date[complex_date] = csv.writer(
                    csvs_by_date[complex_date], delimiter="|")
                headers_1 = self.build_headers("drug", need_return=True)
                headers_2 = self.build_headers("rx", need_return=True)
                headers_1.extend(headers_2)
                buffers_by_date[complex_date].writerow(headers_1)

            available_data["iso_year"] = iso_year
            available_data["iso_week"] = iso_week
            available_data["iso_day"] = iso_day
            available_data["iso_delegation"] = iso_delegation
            available_data["year"] = year
            available_data["month"] = month
            available_data["date_created"] = available_data.get(
                "date_release") or available_data.get("date_visit")
            available_data["date_closed"] = available_data.get("date_delivery")
            self.months.add((year, month))

            available_data, error = self.calculate_delivered(available_data)
            if error:
                self.append_missing_row(row, error)
                continue
            delivered = available_data.get("delivered_id")
            delivered_write = None
            if classify_id:
                delivered_write = available_data.get("clasif_assortment_presc")

            available_data = self.generic_match("medicament", available_data)

            folio_document = available_data.get("folio_document")
            if not folio_document:
                error = "Folio Documento; No se encontró folio documento"
                self.append_missing_row(row, error)
                continue

            folio_ocamis = "|".join([
                str(self.entity_id),
                str(iso_year),
                str(iso_week),
                str(iso_delegation) or '0',
                folio_document])
            if len(folio_ocamis) > 64:
                error = "Folio Ocamis; El folio ocamis es muy largo"
                self.append_missing_row(row, error)
                continue
            curr_rx = all_rx.get(complex_date, {}).get(folio_ocamis)
            if curr_rx:
                available_data["rx_id"] = curr_rx["uuid_folio"]
                all_delivered = curr_rx.get("all_delivered", set())
                all_delivered.add(delivered)
                curr_rx["all_delivered"] = all_delivered
                if classify_id:
                    all_delivered_write = curr_rx.get(
                        "all_delivered_write", set())
                    all_delivered_write.add(delivered_write)
                    curr_rx["all_delivered_write"] = all_delivered_write
                else:
                    all_delivered_write = set()
                delivered_final_id, error = calculate_delivered_final(
                    all_delivered, all_delivered_write)
                if error:
                    if "clasificación" in error:
                        value = error.split("; ")[1]
                        self.append_missing_field(
                            row, classify_id, value, error=delivered_final_id,
                            drug_uuid=uuid)
                curr_rx["delivered_final_id"] = delivered_final_id
                all_rx[complex_date][folio_ocamis] = curr_rx
            else:
                uuid_folio = str(uuid_lib.uuid4())
                available_data["uuid_folio"] = uuid_folio
                available_data["rx_id"] = uuid_folio
                available_data["delivered_final_id"] = delivered
                available_data["folio_ocamis"] = folio_ocamis
                available_data["folio_document"] = folio_document
                available_data["all_delivered"] = {delivered}
                if delivered_write:
                    available_data["all_delivered_write"] = {delivered_write}

                for cat_name in rx_cats:
                    available_data = self.generic_match(cat_name, available_data)

                all_rx[complex_date][folio_ocamis] = available_data
                curr_rx = available_data

            current_drug_data = []
            self.last_valid_row = available_data.copy()
            for drug_field in self.model_fields["drug"]:
                value = available_data.get(drug_field["name"], None)
                if value is None:
                    value = locals().get(drug_field["name"])
                # value = available_data.get(drug_field, locals().get(drug_field))
                current_drug_data.append(value)
            current_rx_data = []
            # curr_rx = all_rx.get(folio)
            for field_rx in self.model_fields["rx"]:
                value = curr_rx.get(field_rx["name"], None)
                if value is None:
                    value = locals().get(field_rx["name"])
                current_rx_data.append(value)
            current_drug_data.extend(current_rx_data)
            # self.buffers["rx"][week].writerow(current_rx_data)
            # all_data = current_rx_data.extend(current_drug_data)
            buffers_by_date[complex_date].writerow(current_drug_data)
            success_drugs_count += 1
            totals_by_date[complex_date]["drugs_count"] += 1
            # if len(all_rx) > self.sample_size:
            #     break
        report_errors = self.build_report()
        rx_count = 0
        for complex_date, folios in all_rx.items():
            len_folios = len(folios)
            rx_count += len_folios
            totals_by_date[complex_date]["rx_count"] += len_folios
        report_errors["rx_count"] = rx_count
        report_errors["drugs_count"] = success_drugs_count
        report_errors["processed_count"] = processed_count
        report_errors["total_count"] = total_count
        report_errors["discarded_count"] = discarded_count
        for med_cat in self.med_cat_models:
            cat_name = med_cat["name"]
            report_errors[f"{cat_name}_count"] = len(self.cat_keys[cat_name]) \
                if self.cat_keys.get(cat_name) else 0
        all_months = [[year, month] for (year, month) in self.months]
        result_data = {
            "report_errors": report_errors,
            "is_prepare": self.is_prepare,
            "sheet_file_id": self.sheet_file_id,
            "lap_sheet_id": self.lap_sheet_id,
            "all_months": all_months,
        }
        if self.is_prepare:
            # return json.dumps(result_data)
            return result_data

        self.buffers["missing_field"].writerows(self.all_missing_fields)
        self.buffers["missing_row"].writerows(self.all_missing_rows)
        all_final_paths = []

        for elem_list in self.normal_models:
            cat_name = elem_list["name"]
            if "missing" in cat_name:
                cat_count = report_errors.get(f"{cat_name}s", 0)
            else:
                cat_count = report_errors.get(f"{cat_name}_count", 0)
            if cat_count == 0:
                continue
            only_name = self.final_path.replace("NEW_ELEM_NAME", cat_name)
            all_final_paths.append({
                "model": elem_list["model"],
                "path": only_name,
            })
            self.s3_utils.save_file_in_aws(self.csvs[cat_name].getvalue(), only_name)
        for complex_date in csvs_by_date.keys():
            iso_year, iso_week, iso_delegation, year, month = complex_date
            # elem_list = [iso_year, iso_week, iso_delegation, year, month]
            elem_list = list(map(str, list(complex_date)))
            complement = '_'.join(elem_list)
            elem_name = f"by_week_{complement}"
            # elem_name = f"by_week_{iso_year}_{iso_week}_{year}_{month}"
            only_name = self.final_path.replace("_NEW_ELEM_NAME", elem_name)
            only_name = only_name.replace("NEW_ELEM_NAME", "by_week")
            all_final_paths.append({
                "path": only_name,
                "iso_year": iso_year,
                "iso_week": iso_week,
                "year_week": f"{iso_year}-{iso_week:02d}",
                "iso_delegation_id": iso_delegation,
                "year": year,
                "month": month,
                "year_month": f"{year}-{month:02d}",
                "drugs_count": totals_by_date[complex_date]["drugs_count"],
                "rx_count": totals_by_date[complex_date]["rx_count"],
            })
            self.s3_utils.save_file_in_aws(
                csvs_by_date[complex_date].getvalue(), only_name)

        result_data["final_paths"] = all_final_paths
        result_data["decode"] = self.decode
        return result_data

    def special_division(self, row_data):
        fragments = []

        def build_blocks(re_field, remain_data):
            print("remain_data", remain_data)
            regex = re_field["regex"]
            print("regex", regex)
            results = re.split(regex, remain_data, 1)
            if len(results) == 1:
                results.extend(["", ""])
            elif len(results) == 2:
                results.append("")
            return results, re_field["position"]

        prev_pos = None
        next_pos = 1
        remain_block = row_data
        for idx, regex_field in enumerate(self.regex_fields):
            prev_pos = next_pos if prev_pos is not None else 0
            res, next_pos = build_blocks(regex_field, remain_block)

            [current_block, same, remain_block] = res
            block_fields = [field for field in self.positioned_fields
                            if prev_pos < field["position"] < next_pos]
            len_block_fields = len(block_fields)
            if len_block_fields == 0:
                if same:
                    fragments.append(same)
                continue
            position_separator = None
            for idx_block, block_field in enumerate(block_fields):
                same_separator = block_field.get("same_separator")
                # if block_field.get("clean_function") == "same_separator":
                if same_separator:
                    if position_separator is None:
                        position_separator = idx_block
                    else:
                        return row_data
            # fields_with_separator = [field for field in block_fields
            #                          if field.get("clean_function") == "same_separator"]
            # some_has_separator = any(fields_with_separator)
            # len_with_separator = len(fields_with_separator)
            if position_separator is None:
                block_values = current_block.split(self.delimit)
            else:
                normal_way_count = position_separator
                reverse_way_count = len_block_fields - position_separator - 1
                # total_processed = 0
                block_values = []
                for normal_seq in range(normal_way_count):

                    try:
                        [block_value, current_block] = current_block.split(
                            self.delimit, 1)
                    except ValueError:
                        return row_data
                    block_values.append(block_value)
                for reverse_seq in range(reverse_way_count):
                    try:
                        [current_block, block_value] = current_block.rsplit(
                            self.delimit, 1)
                        block_values.insert(normal_way_count, block_value)
                    except ValueError:
                        return row_data
                block_values.insert(normal_way_count, current_block)
            fragments.extend(block_values)
            if same:
                fragments.append(same)

        return fragments

    def divide_rows(self, data_rows):
        structured_data = []
        sample = data_rows[:50]
        self.decode = self.decode or obtain_decode(sample)
        if self.decode == "latin-1":
            self.decode_final = 'latin-1'

        if self.decode == "unknown":
            error = "No se pudo decodificar el archivo"
            return [], [error], None

        # for row_seq, row in enumerate(data_rows[begin+1:], start=begin+1):
        for row_seq, row in enumerate(data_rows, start=1):
            self.last_missing_row = None
            if self.is_prepare:
                row_final = [col.replace('\r\n', '').strip() for col in row]
                row_data = row_final
            else:
                row_decode = row.decode(self.decode) if self.decode != "str" else str(row)
                # .replace('\r\n', '')
                row_data = row_decode.replace('\r\n', '')
                row_final = row_data.split(self.delimit)
                row_final = [col.strip() for col in row_final]
            current_count = len(row_final)

            if self.some_same_separator and current_count > self.columns_count:
                row_final = self.special_division(row_data)
                current_count = len(row_final)

            if current_count == self.columns_count:
                row_final.insert(0, str(row_seq))
                structured_data.append(row_final)
            else:
                error = "Conteo distinto de Columnas; %s de %s" % (
                    current_count, self.columns_count)
                row_data = [str(row_seq), row_data]
                self.append_missing_row(row_data, error)

        return structured_data

    def build_special_cols(self, all_data):

        def get_columns_by_type(column_type):
            return [col for col in self.existing_fields
                    if col["column_type"] == column_type]

        return {
            "built": self.get_built_cols(),
            "divided": self.get_divided_cols(),
            "global": get_columns_by_type("global"),
            "tab": get_columns_by_type("tab"),
            "file_name": get_columns_by_type("file_name"),
            "ceil": self.get_ceil_cols(all_data),
            "copy_from_up": self.copy_from_up,
        }

    def string_time_to_regex(self, string_time):
        conversion_map = {
            '%Y': r'\d{4}',
            '%m': r'\d{2}',
            '%d': r'\d{2}',
            '%H': r'\d{2}',
            '%M': r'\d{2}',
            '%S': r'\d{2}',
            '%f': r'\d{3,6}',
            ' ': r'\s',
            '-': r'-',
            ':': r':',
            '.': r'.',
        }

        regex_pattern = string_time
        for key, value in conversion_map.items():
            regex_pattern = regex_pattern.replace(key, value)
        regex_pattern = f"{self.sep}?({regex_pattern}){self.sep}?"
        return regex_pattern

    def get_built_cols(self):
        built_cols = []
        base_built_cols = [col for col in self.existing_fields
                           if col["column_type"] == "built"]
        for built_col in base_built_cols:
            origin_cols = [col for col in self.existing_fields
                           if col["child"] == built_col["name_column"]]
            # origin_cols = sorted(origin_cols, key=lambda x: x.get("t_value"))
            origin_cols = sorted(origin_cols, key=lambda x: x.get("fragmented"))
            built_col["origin_cols"] = origin_cols
            built_cols.append(built_col)
        return built_cols

    def get_divided_cols(self):
        divided_cols = []
        base_divided_cols = [col for col in self.existing_fields
                             if col["column_type"] == "divided"]
        unique_parents = list(set([col["name_column"]
                                   for col in base_divided_cols]))
        for parent in unique_parents:
            try:
                parent_col = [col for col in self.existing_fields
                              if col["name_column"] == parent][0]
            except IndexError:
                continue
            destiny_cols = [col for col in base_divided_cols
                            if col["name_column"] == parent]
            # destiny_cols = sorted(destiny_cols, key=lambda x: x.get("t_value"))
            destiny_cols = sorted(
                destiny_cols, key=lambda x: x.get("only_params_parent"))
            parent_col["destiny_cols"] = destiny_cols
            divided_cols.append(parent_col)
        return divided_cols

    def get_ceil_cols(self, all_data):
        ceil_cols = []
        ceil_excel_cols = [col for col in self.existing_fields
                           if col["column_type"] == 'ceil_excel']
        for col in ceil_excel_cols:
            # ceil = col.get("t_value")
            ceil = col.get("get_ceil")
            if not ceil:
                continue
            row_position = int(ceil[1:])
            col_position = ord(ceil[0]) - 64
            col["final_value"] = all_data[row_position - 1][col_position]
            ceil_cols.append(col)
        return ceil_cols

    def special_available_data(self, available_data, row, special_cols):

        for built_col in special_cols["built"]:
            origin_values = []
            for origin_col in built_col["origin_cols"]:
                if origin_col.get("position"):
                    origin_values.append(row[origin_col["position"]])
                elif origin_col.get("final_value"):
                    origin_values.append(origin_col["final_value"])
                else:
                    raise Exception("No se puede construir la columna")
            # concat_char = built_col.get("t_value", "")
            concat_char = built_col.get("only_params_child")
            built_value = concat_char.join(origin_values)
            available_data[built_col["name"]] = built_value

        for divided_col in special_cols["divided"]:
            # divided_char = divided_col.get("t_value")
            divided_char = divided_col.get("concatenated")
            if not divided_char:
                continue
            origin_value = row[divided_col["position"]]
            destiny_cols = divided_col["destiny_cols"]
            split_count = len(destiny_cols) - 1
            divided_values = origin_value.split(divided_char, split_count)
            for i, divided_value in enumerate(divided_values, start=1):
                destiny_col = destiny_cols[i - 1]
                available_data[destiny_col["name"]] = divided_value

        for global_col in special_cols["global"]:
            global_value = global_col.get("global_variable")
            # available_data[global_col["name"]] = global_col["t_value"]
            available_data[global_col["name"]] = global_value

        for tab_col in special_cols["tab"]:
            available_data[tab_col["name"]] = self.sheet_name

        for file_name_col in special_cols["file_name"]:
            available_data[file_name_col["name"]] = self.file_name_simple

        for ceil_col in special_cols["ceil"]:
            available_data[ceil_col["name"]] = ceil_col["final_value"]
        return available_data

    def complement_available_data(self, available_data, row):
        from datetime import datetime, timedelta
        import re

        some_date = None
        uuid = available_data.get("uuid")
        # fields_with_name = [field for field in self.existing_fields
        #                     if field["name"] and field["position"]]
        # fields_with_name = [field for field in self.existing_fields
        #                     if field["name"]]
        # for field in fields_with_name:
        self.example_count += 1
        for field in self.existing_fields:
            error = None
            if field.get("position"):
                value = row[field["position"]]
            else:
                value = available_data.get(field["name"])
            null_to_value = field.get("null_to_value")
            if null_to_value:
                if value is None or value == "":
                    value = null_to_value
            same_group_data = field.get("same_group_data")
            copied = False
            # if self.example_count < 15:
            #     print("------------------")
            #     print("field:", field.get("name"))
            #     print("value:", value)
            #     print("last_valid_row:", self.last_valid_row)
            #     print("same_group_data:", same_group_data)
            if not value and same_group_data and self.last_valid_row:
                value = self.last_valid_row.get(field["name"])
                copied = True
                if field["data_type"] == "Datetime" and value:
                    some_date = value
            # if self.example_count < 15:
            #     print("value final:", value)
            if not value:
                continue
            if "almost_empty" in field:
                value = None
            elif "text_nulls" in field:
                text_nulls = field["text_nulls"]
                if not isinstance(text_nulls, str):
                    raise Exception("La transformación de NULOS no puede estar vacía")
                text_nulls = text_nulls.split(",")
                text_nulls = [text_null.strip() for text_null in text_nulls]
                if value in text_nulls:
                    if null_to_value:
                        value = null_to_value
                    else:
                        value = None
            if field.get("duplicated_in"):
                duplicated_in = field["duplicated_in"]
                some_almost_empty = False
                has_child = field.get("child")
                # if field.get("clean_function") == "almost_empty":
                if "almost_empty" in field:
                    some_almost_empty = True
                if not some_almost_empty:
                    dupl_almost_empty = duplicated_in.get("almost_empty")
                    # if duplicated_in.get("clean_function") == "almost_empty":
                    if dupl_almost_empty:
                        some_almost_empty = True
                if some_almost_empty or has_child:
                    pass
                else:
                    duplicated_value = row[duplicated_in["position"]]
                    if duplicated_value != value:
                        error = f"El valor de las columnas que apuntan a " \
                                f"{field['name']} no coinciden"
            try:
                if not value:
                    pass
                elif copied:
                    pass
                elif field["data_type"] == "Datetime":  # and not is_same_date:
                    if value == self.last_date and value:
                        value = self.last_date_formatted
                        # print("same", value)
                    else:
                        # print("case")
                        if self.string_date == "MANY":
                            format_date = field.get("format_date").split(";")
                            string_dates = [date.strip() for date in format_date]
                        else:
                            string_dates = self.string_dates
                        is_success = False
                        # print("value initial:", value)
                        for string_format in string_dates:
                            # print("string_format", string_format)
                            try:
                                if string_format == "EXCEL":
                                    days = int(value)
                                    seconds = (float(value) - days) * 86400
                                    seconds = round(seconds)
                                    value = datetime(1899, 12, 30) + timedelta(
                                        days=days, seconds=seconds)
                                elif string_format == "UNIX":
                                    value = datetime.fromtimestamp(value)
                                else:
                                    value = datetime.strptime(value, string_format)
                                    # print("value final: ", value)
                                self.last_date = value
                                self.last_date_formatted = value
                                is_success = True
                                break
                            except ValueError:
                                pass
                            except TypeError:
                                pass
                        if not is_success:
                            error = "No se pudo convertir la fecha"
                    # else:
                    #     self.last_date = value
                    #     value = datetime.strptime(value, self.string_date)
                    #     self.last_date_formatted = value
                    if not some_date or field["name"] == "date_delivery":
                        some_date = value
                        # print("some_date", some_date)
                elif field["data_type"] == "Integer":
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = int(float(value))
                        except Exception:
                            error = "No se pudo convertir a número entero"
                    except Exception:
                        error = "No se pudo convertir a número entero"
                    if not error and value < 0:
                        error = "El valor no puede ser negativo"
                elif field["data_type"] == "Float":
                    value = float(value)
                else:
                    value = str(value)
            except ValueError:
                error = "No se pudo convertir a %s" % field["data_type"]
            if value and not error:
                regex_format = field.get("regex_format")
                if regex_format:
                    if not re.match(regex_format, value):
                        error = "No se validó con el formato de %s" % field["name"]
                elif field.get("max_length"):
                    if len(value) > field["max_length"]:
                        error = "El valor tiene más de los caracteres permitidos"
                # clean_function = field.get("clean_function")
                # if clean_function:
                #     if clean_function == "almost_empty":
                #         value = None
                #     elif clean_function == "text_nulls":
                #         if value == field.get("t_value"):
                #             value = None
            if error:
                self.append_missing_field(
                    row, field["name_column"], value, error=error, drug_uuid=uuid)
                value = None
            available_data[field["name"]] = value
        # if not some_date:
        #     print("some_date al final?", some_date)
        return available_data, some_date

    def build_headers(self, cat_name, need_return=False):
        fields = self.model_fields[cat_name]
        headers = [field["name"] for field in fields]
        if need_return:
            return headers
        else:
            self.buffers[cat_name].writerow(headers)

    def generic_match(self, cat_name, available_data, is_first=False):
        import hashlib
        flat_fields = self.med_cat_flat_fields.get(cat_name, {})
        init_values = self.initial_data.get(cat_name, {})
        initial_all_values = init_values.get("all_values", []).copy()
        initial_data_values = init_values.get("data_values", []).copy()
        all_values = []
        data_values = []
        is_med_unit = cat_name == "medical_unit"
        is_medicament = cat_name == "medicament"
        for flat_field in flat_fields:
            field_name = flat_field["name"]
            value = available_data.get(f"{cat_name}_{field_name}", None)
            if value and is_medicament:
                if field_name == "key2":
                    value = value.replace(".", "")
                if field_name == "own_key2":
                    all_values[0] = self.entity_id
            elif is_med_unit and not value:
                value = flat_field["default_value"]
            if value is not None:
                str_value = value if flat_field["is_string"] else str(value)
                data_values.append(str_value)
            all_values.append(value)

        def add_hash_to_cat(hash_key, flat_values):
            if is_first or hash_key not in self.cat_keys[cat_name]:
                every_values = [hash_key] + initial_all_values + flat_values
                self.buffers[cat_name].writerow(every_values)
                self.cat_keys[cat_name].add(hash_key)

        if not data_values:
            hash_id = None
            # if is_first:
            #     add_hash_to_cat(self.hash_null, all_values)
        else:
            final_data_values = initial_data_values + data_values
            value_string = "".join(final_data_values)
            value_string = value_string.encode(self.decode_final)
            hash_id = hashlib.md5(value_string).hexdigest()
            add_hash_to_cat(hash_id, all_values)
        available_data[f"{cat_name}_id"] = hash_id
        return available_data

    def calculate_delivered(self, available_data):
        available_delivered = [
            "ATENDIDA", "CANCELADA", "NEGADA", "PARCIAL", "SURTIDO COMPLET0",
            "SURTIDO INCOMPLETO", "RECETA NO SURTIDA", "SURTIDO COMPLETO",
            "SURTIDA PARC O NO SURTIDA", "SURTIDA", "EN CEROS", "COMPLETA",
            "SURTIDO COMPLET", "NEGADO"]
        # DISPENSADA, NO DISPENSADA

        class_presc = available_data.get("clasif_assortment")
        if not class_presc:
            class_presc = available_data.get("clasif_assortment_presc")
        else:
            class_presc = text_normalizer(class_presc)
        is_cancelled = class_presc == "CANCELADA"
        if class_presc:
            if class_presc not in available_delivered:
                error = f"Clasificación de surtimiento no contemplada; {class_presc}"
                return available_data, error
        prescribed_amount = available_data.get("prescribed_amount")

        def identify_errors(av_data, amount, err_text):
            err = None
            if amount is None:
                if is_cancelled:
                    av_data["prescribed_amount"] = available_data.get(
                        "prescribed_amount", 0)
                    av_data["delivered_amount"] = available_data.get(
                        "delivered_amount", 0)
                    av_data["delivered_id"] = "cancelled"
                elif self.global_delivered:
                    pass
                else:
                    err = f"No se puede determinar el status de entrega; " \
                          f"No encontramos la cantidad {err_text}"
            elif amount > 30000:
                err = f"Existe una cantidad inusualmente alta; cantidad {err_text}"
            elif amount < 0:
                err = f"Existe una cantidad negativa; cantidad {err_text}"
            return av_data, err

        available_data, error = identify_errors(
            available_data, prescribed_amount, "prescrita")
        if error or available_data.get("delivered_id"):
            return available_data, error

        delivered_amount = available_data.get("delivered_amount")

        if delivered_amount is None:
            not_delivered_amount = available_data.pop("not_delivered_amount", None)
            if not_delivered_amount is not None:
                delivered_amount = prescribed_amount - not_delivered_amount
                available_data["delivered_amount"] = delivered_amount

        available_data, error = identify_errors(
            available_data, delivered_amount, "entregada")
        if error or available_data.get("delivered_id"):
            return available_data, error
        if self.global_delivered:
            available_data["delivered_id"] = self.global_delivered
            return available_data, None
        if prescribed_amount == delivered_amount:
            if is_cancelled:
                delivered = "cancelled"
            elif prescribed_amount == 0:
                delivered = "zero"
            else:
                delivered = "complete"
        elif not delivered_amount:
            if is_cancelled:
                delivered = "cancelled"
            else:
                delivered = "denied"
        elif delivered_amount < prescribed_amount:
            delivered = "partial"
        elif delivered_amount > prescribed_amount:
            delivered = "over_delivered"
        elif is_cancelled:
            delivered = "cancelled"
        else:
            return available_data, "No se puede determinar el status de entrega"
        available_data["delivered_id"] = delivered
        return available_data, None

    def delegation_match(self, available_data):
        if not self.split_by_delegation:
            return None, None, None
        delegation_name = available_data.get("medical_unit_delegation_name", None)
        delegation_id = None
        delegation_id2 = None
        delegation_error = None
        if delegation_name:
            delegation_name = text_normalizer(delegation_name)
            try:
                delegation_id = self.delegation_cat[delegation_name]
            except Exception:
                delegation_error = f"No se encontró la delegación;" \
                                   f" {delegation_name}"
            if "UMAE " in delegation_name:
                delegation_id2 = self.delegation_cat["TODAS LAS UMAES"]
            else:
                delegation_id2 = delegation_id

        return delegation_id, delegation_id2, delegation_error

    def append_missing_row(self, row_data, error=None, drug_id=None):
        self.last_valid_row = None
        if self.last_missing_row:
            if error:
                self.last_missing_row[-2] = False
                self.last_missing_row[-4] = None
                self.all_missing_rows[-1][-4] = None
                self.all_missing_rows[-1][-1] = error
            return self.all_missing_rows[-1][0]
        last_revised = self.last_revised
        inserted = not bool(error)
        inserted = False
        # row_seq = int(row_data[0])
        # original_data = row_data[1:]
        original_data = json.dumps(row_data)
        missing_data = []
        uuid = str(uuid_lib.uuid4())
        sheet_file_id = self.sheet_file_id
        lap_sheet_id = self.lap_sheet_id
        for field in self.model_fields["missing_row"]:
            value = locals().get(field["name"])
            missing_data.append(value)
        self.last_missing_row = missing_data
        self.all_missing_rows.append(missing_data)
        return uuid

    def append_missing_field(
            self, row, name_column_id, original_value, error, drug_uuid=None):
        missing_row_id = self.append_missing_row(row, drug_id=drug_uuid)
        missing_field = []
        uuid = str(uuid_lib.uuid4())
        inserted = False
        last_revised = self.last_revised
        # if name_column:
        #     name_column = name_column.id
        for field in self.model_fields["missing_field"]:
            value = locals().get(field["name"])
            missing_field.append(value)
        self.all_missing_fields.append(missing_field)

    def build_report(self):
        report_data = {"general_error": ""}
        real_missing_rows = [row for row in self.all_missing_rows if row[-1]]
        report_data["missing_rows"] = len(self.all_missing_rows)
        if real_missing_rows:
            report_data["real_missing_rows"] = len(real_missing_rows)
            row_errors = {}
            error_types_count = 0
            for missing_row in real_missing_rows:
                error = missing_row[-1]
                if not error:
                    continue
                try:
                    [error_type, error_detail] = error.split(";", 1)
                except Exception:
                    # print("error report:", e)
                    [error_type, error_detail] = [error, "GENERAL"]
                if error_type in row_errors:
                    row_errors[error_type]["count"] += 1
                    if error_detail in row_errors[error_type]:
                        row_errors[error_type][error_detail]["count"] += 1
                        example_count = len(
                            row_errors[error_type][error_detail]["examples"])
                        if example_count < 4:
                            row_errors[error_type][error_detail]["examples"].append(
                                missing_row[-3])
                    elif len(row_errors[error_type]) < 20:
                        row_errors[error_type][error_detail] = {
                            "count": 1, "examples": [missing_row[-3]]}
                elif error_types_count < 40:
                    row_errors[error_type] = {
                        "count": 1,
                        error_detail: {
                            "count": 1, "examples": [missing_row[-3]]}
                    }
                    error_types_count += 1
            report_data["row_errors"] = row_errors
            if len(row_errors) > 50:
                report_data["general_error"] += \
                    "Se encontraron más de 50 tipos de errores en las filas"
        else:
            report_data["real_missing_rows"] = 0
            report_data["row_errors"] = {}

        if self.all_missing_fields:
            report_data["missing_fields"] = len(self.all_missing_fields)
            field_errors = {}
            error_types_count = 0
            for missing_field in self.all_missing_fields:
                error = missing_field[-1]
                name_column = missing_field[2]
                original_value = missing_field[3]
                if error in field_errors:
                    field_errors[error]["count"] += 1
                    if name_column in field_errors[error]:
                        field_errors[error][name_column]["count"] += 1
                        examples = field_errors[error][name_column]["examples"]
                        if len(examples) < 6 and original_value not in examples:
                            field_errors[error][name_column]["examples"].append(
                                original_value)
                    else:
                        field_errors[error][name_column] = {
                            "count": 1,
                            "examples": [original_value]
                        }
                elif error_types_count < 40:
                    error_types_count += 1
                    field_errors[error] = {
                        "count": 1,
                        name_column: {
                            "count": 1,
                            "examples": [original_value]
                        }
                    }
            report_data["field_errors"] = field_errors
        else:
            report_data["missing_fields"] = 0
            report_data["field_errors"] = {}

        if not report_data.get("missing_rows"):
            report_data["general_error"] = "No se encontraron errores"
        return report_data
