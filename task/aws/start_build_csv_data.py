from datetime import datetime
import uuid as uuid_lib
import json
import re
from task.aws.common import (
    calculate_delivered_final, send_simple_response, BotoUtils,
    convert_to_str, text_normalizer, DeliveredCalculator,
    ValueProcessError, EarlyResult)
from task.aws.complement import GetAllRows, Buffers, DateTime


# def start_build_csv_data(event, context={"request_id": "test"}):
def lambda_handler(event, context):
    import traceback
    import sys
    try:
        init_data = event["init_data"]
        match_aws = TransformToCsv(init_data, context, event.get("s3"))
    except Exception as e:
        error_ = traceback.format_exc()
        print("Error en la inicialización", error_)
        errors = [f"Hay 1 error raro en la inicialización: {str(e)}", error_]
        return send_simple_response(event, context, errors=errors)

    # try:
    file = event["file"]
    # print("file", file)
    final_result = match_aws.build_csv_to_data(file)
    # except ValueError as e:
    #     errors = [str(e)]
    #     return send_simple_response(event, context, errors=errors)
    # except Exception as e:
    #     error_ = traceback.format_exc()
    #     print("Error en la construcción", error_)
    #     errors = [f"Hay un error raro en la construcción: \n{str(e)}\n{error_}"]
    #     return send_simple_response(event, context, errors=errors)

    return send_simple_response(event, context, result=final_result)


class TransformToCsv:
    med_cat_flat_fields = {}
    initial_data = {}

    # Only to get_all_rows
    delimiter = None
    columns_count = None

    provider_id = None
    existing_fields = None

    special_cols = None
    sheet_file_id = None
    lap_sheet_id = None
    final_path = None
    split_by_delegation = False
    global_transformations = []
    decode = None
    row_start_data = 0
    hash_null = None
    string_date = None

    available_deliveries = {}
    delegation_cat = {}
    sheet_name = None
    file_name_simple = None

    def __init__(self, init_data: dict, context, s3):
        self.models_to_save = ["drug", "rx", "unique_helpers"]
        self.examples_count = 0
        self.limit_examples = 0

        self.sample_count = 0
        self.months = set()
        self.last_revised = datetime.now()
        self.rx_cats = []
        self.required_cols = []
        self.global_delegation = None
        self.global_delivered = None
        self.real_models = None
        self.global_clues = None
        self.model_fields = {}
        self.cat_keys = {}
        self.med_cat_models = []
        self.decode_final = 'utf-8'
        self.last_missing_row = None
        self.all_missing_rows = []
        self.last_valid_row = None
        self.errors_count = 0
        self.is_prepare = False

        self.some_date = None
        # self.unique_helpers = ["medicament_key", "medical_unit_key"]

        for key, value in init_data.items():
            setattr(self, key, value)

        self.model_fields["unique_helpers"] = [
            {"name": "medicament_key", "is_relation": False},
            {"name": "medical_unit_key", "is_relation": False},
        ]

        self.date_time = DateTime(init_data["string_date"])

        self.not_unicode = "not_unicode" in self.global_transformations
        self.editable_models = init_data["editable_models"]

        self.build_cats()
        self.special_fields = [field for field in self.existing_fields
                               if field.get("is_special")]
        self.copy_from_up = [field for field in self.existing_fields
                             if field.get("same_group_data")]
        amount_fields = [field for field in self.existing_fields
                         if "_amount" in field["name"] or
                         "clasif_assortment" in field["name"]]

        classify_cols = [col for col in self.existing_fields
                         if col["name"] == "clasif_assortment_presc"]
        self.classify_id = classify_cols[0]["name_column"] if classify_cols else None

        check_rows = "no_valid_row_data" in self.global_transformations
        if check_rows:
            self.required_cols = [col for col in self.existing_fields
                                  if col["required_row"]]
        self.copy_invalid_rows = "copy_invalid_rows" in self.global_transformations

        if len(amount_fields) == 1:
            amount_field = amount_fields[0]
            if amount_field["name"] == "delivered_amount":
                self.global_delivered = "only_delivered"
            elif amount_field["name"] == "prescribed_amount":
                self.global_delivered = "only_prescribed"

        self.delivered = DeliveredCalculator(
            self.global_delivered, self.available_deliveries)
        self.s3_utils = BotoUtils(s3)
        self.real_buffers = Buffers(
            self, self.model_fields, self.models_to_save, self.final_path)

        self.context = context

    def show_examples(self, draw_line=True):
        self.examples_count += 1
        in_limit = self.examples_count < self.limit_examples
        if in_limit and draw_line:
            print("")
        return in_limit

    def build_cats(self):
        complement_models = {
            "ComplementDrug": "complement_drug",
            "ComplementRx": "complement_rx",
        }
        for formal_name, model_name in complement_models.items():
            if formal_name in self.real_models:
                self.models_to_save.append(model_name)
        if "Diagnosis" in self.real_models:
            self.models_to_save.append("diagnosis_rx")

        # print("\nmodels_to_save 1.2", self.models_to_save, "\n")

        # if self.show_examples():
        #     print("real_models\n", self.real_models, "\n")
        #     print("editable_models:\n", self.editable_models)
        for cat in self.editable_models:
            # print("cat:", cat)
            cat_name = cat["name"]
            if cat.get("app") == "med_cat":
                self.med_cat_models.append(cat)
            if cat["model"] not in self.real_models:
                continue
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
                field["default_value"] = None
                if field["is_relation"]:
                    if field_name == "provider_id" and not is_medicament:
                        value = self.provider_id
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
            self.initial_data[cat_name] = {
                "data_values": data_values, "all_values": all_values}
            # print("cat to set", cat_name)
            self.cat_keys[cat_name] = set()
            # self.generic_match(cat_name, {}, True)

            if cat_name != "medicament" and cat["app"] == "med_cat":
                self.rx_cats.append(cat_name)
        # print("med_cat_flat_fields: \n", self.med_cat_flat_fields)
        # print("rx_cats: \n", self.rx_cats)

    def build_csv_to_data(self, file):

        all_rows = GetAllRows(self)(file)

        self.real_buffers.add_count("total_count", len(all_rows))
        self.real_buffers.add_count("discarded_count", self.row_start_data - 1)

        self.special_cols = self.build_special_cols(all_rows)

        for row in all_rows[self.row_start_data - 1:]:
            self.process_row(row)

        # report_errors = self.build_report()
        self.real_buffers.count_rx()
        # print("self.med_cat_models", self.med_cat_models)
        for med_cat in self.med_cat_models:
            cat_name = med_cat["name"]
            count = len(self.cat_keys.get(cat_name, {}))
            # print(f"med_cat {cat_name}; count:", count)
            self.real_buffers.add_count(f"{cat_name}_count", count)

        result_data = {
            "report_errors": self.real_buffers.data_report,
            "all_months": [[year, month] for (year, month) in self.months],
        }
        for field in ["is_prepare", "sheet_file_id", "lap_sheet_id"]:
            result_data[field] = getattr(self, field)

        if self.is_prepare:
            return result_data

        self.real_buffers.save_missing_rows(self.all_missing_rows)
        self.real_buffers.save_csv_cats()
        self.real_buffers.save_csvs_by_date()

        result_data["final_paths"] = self.real_buffers.all_final_paths
        result_data["decode"] = self.decode
        return result_data

    def process_row(self, row):
        # is_same_date = False
        is_row_invalid = False
        if self.required_cols:
            is_row_invalid = any([col for col in self.required_cols
                                 if not row[col["position"]]])
            if not self.copy_invalid_rows and is_row_invalid:
                self.real_buffers.add_count("discarded_count")
                return

        self.last_missing_row = None

        uuid = str(uuid_lib.uuid4())
        available_data = {
            "provider_id": self.provider_id,
            "sheet_file_id": self.sheet_file_id,
            "lap_sheet_id": self.lap_sheet_id,
            "row_seq": int(row[0]),
            "uuid": uuid,
        }

        available_data = self.special_available_data(available_data, row)

        self.some_date = None
        for field in self.existing_fields:
            try:
                value = self.basic_available_data(available_data, row, field)
            except ValueProcessError as e:
                if not is_row_invalid:
                    name_col = field["name_column"]
                    self.add_missing_field(row, name_col, e.value,
                                           str(e), drug_uuid=uuid)
                value = None
            field_name = field["name"]
            available_data[field_name] = value

        # se van a considerar para el siguiente valor, pero no se procesará
        if is_row_invalid and self.copy_invalid_rows:
            self.last_valid_row = available_data.copy()
            self.real_buffers.add_count("discarded_count")
            return

        if "complement_drug" in self.models_to_save:
            available_data["uuid_comp_drug"] = str(uuid_lib.uuid4())
            available_data["drug_id"] = uuid

        self.real_buffers.add_count("processed_count")
        if not self.some_date:
            error = "No se pudo convertir ninguna fecha; sin ejemplos"
            return self.add_missing_row(row, error)

        try:
            complex_date, folio_ocamis = self.calculate_iso(available_data)
        except NotImplementedError as e:
            return self.add_missing_row(row, str(e))
        except Exception as e:
            return self.add_missing_row(row, str(e))

        try:
            delivered, available_data = self.delivered(available_data)
        except EarlyResult as e:
            delivered = e.delivered
            available_data = e.result
            if e.warning:
                self.add_missing_field(
                    row, self.classify_id, e.delivered, error=e.warning,
                    drug_uuid=uuid)
        except ValueProcessError as e:
            return self.add_missing_row(row, f"{e.message}; {e.value}")

        delivered_write = None
        if self.classify_id:
            delivered_write = available_data.get("clasif_assortment_presc")

        available_data = self.generic_match("medicament", available_data)

        self.real_buffers.add_complex_date(complex_date)
        curr_rx = self.real_buffers.get_rx_data(complex_date, folio_ocamis)

        if curr_rx:
            uuid_folio = curr_rx["uuid"]
            # available_data["uuid_folio"] = uuid_folio
            available_data["rx_id"] = uuid_folio
            all_delivered = curr_rx.get("all_delivered", set())
            all_delivered.add(delivered)
            curr_rx["all_delivered"] = all_delivered
            if self.classify_id:
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
                    self.add_missing_field(
                        row, self.classify_id, value, error=delivered_final_id,
                        drug_uuid=uuid)
            curr_rx["delivered_final_id"] = delivered_final_id
            self.real_buffers.add_rx(complex_date, folio_ocamis, curr_rx)
        else:
            uuid_folio = str(uuid_lib.uuid4())
            # available_data["uuid_folio"] = uuid_folio
            available_data["rx_id"] = uuid_folio
            if "complement_rx" in self.models_to_save:
                available_data["uuid_comp_rx"] = str(uuid_lib.uuid4())
            # if "diagnosis_rx" in self.models_to_save:
            #     available_data["uuid_diag_rx"] = str(uuid_lib.uuid4())

            available_data["delivered_final_id"] = delivered
            available_data["folio_ocamis"] = folio_ocamis
            available_data["all_delivered"] = {delivered}
            if delivered_write:
                available_data["all_delivered_write"] = {delivered_write}

            for cat_name in self.rx_cats:
                available_data = self.generic_match(cat_name, available_data)

            self.real_buffers.add_rx(complex_date, folio_ocamis, available_data)

        current_row_data = []
        self.last_valid_row = available_data.copy()
        for model_name in self.models_to_save:
            is_diagnosis_rx = model_name == "diagnosis_rx"
            is_complement = "complement" in model_name or is_diagnosis_rx
            for field in self.model_fields[model_name]:
                field_name = field["name"]
                value = available_data.get(field_name, None)
                if value is None and is_complement:
                    value = available_data.get(f"{model_name}_{field_name}", None)
                if value is None:
                    value = locals().get(field_name, None)
                # if is_diagnosis_rx and field_name == "is_main":
                current_row_data.append(value)

        self.real_buffers.write_drug_row(complex_date, current_row_data)

    def build_special_cols(self, all_rows):
        if self.special_cols:
            return self.special_cols

        def get_columns_by_type(column_type):
            return [col for col in self.existing_fields
                    if col["column_type"] == column_type]

        return {
            "built": self.get_built_cols(),
            "divided": self.get_divided_cols(),
            "global": get_columns_by_type("global"),
            "tab": get_columns_by_type("tab"),
            "file_name": get_columns_by_type("file_name"),
            "ceil": self.get_ceil_cols(all_rows),
            "copy_from_up": self.copy_from_up,
        }

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
        # unique_parents_prev = list(set([col["name_column"]
        #                            for col in base_divided_cols]))
        unique_parents = list(set([col["parent"]
                                   for col in base_divided_cols]))
        # print("unique_parents", unique_parents)
        for parent in unique_parents:
            try:
                parent_col = [col for col in self.existing_fields
                              if col["name_column"] == parent][0]
            except IndexError:
                continue
            destiny_cols = [col for col in base_divided_cols
                            if col["parent"] == parent]
            destiny_cols = sorted(
                destiny_cols, key=lambda x: x.get("only_params_parent"))
            parent_col["destiny_cols"] = destiny_cols
            divided_cols.append(parent_col)
        return divided_cols

    def get_ceil_cols(self, all_rows):
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
            col["final_value"] = all_rows[row_position - 1][col_position]
            ceil_cols.append(col)
        return ceil_cols

    def special_available_data(self, available_data, row):

        for built_col in self.special_cols["built"]:
            origin_values = []
            for origin_col in built_col["origin_cols"]:
                if origin_col.get("position"):
                    origin_values.append(row[origin_col["position"]])
                elif origin_col.get("final_value"):
                    origin_values.append(origin_col["final_value"])
                elif origin_col.get("global_variable"):
                    origin_values.append(origin_col["global_variable"])
                else:
                    raise Exception("No se puede construir la columna")
            # concat_char = built_col.get("t_value", "")
            concat_char = built_col.get("only_params_child")
            if concat_char is True:
                concat_char = ""
            built_value = concat_char.join(origin_values)
            available_data[built_col["name"]] = built_value

        for divided_col in self.special_cols["divided"]:
            # divided_char = divided_col.get("t_value")
            divided_char = divided_col.get("concatenated")
            if not divided_char:
                continue
            origin_value = row[divided_col["position"]]
            if text_nulls := divided_col.get("text_nulls"):
                text_nulls = text_nulls.split(",")
                text_nulls = [text_null.strip() for text_null in text_nulls]
                # Si hay que convertir a null y null tiene valor, se vale
                if origin_value in text_nulls:
                    null_to_value = get_null_to_value(divided_col)
                    origin_value = null_to_value
            if origin_value is None:
                continue
            destiny_cols = divided_col["destiny_cols"]
            split_count = len(destiny_cols) - 1
            divided_values = origin_value.split(divided_char, split_count)
            for idx, divided_value in enumerate(divided_values, start=0):
                value = divided_value.strip()
                destiny_col = destiny_cols[idx]
                if destiny_col.get("is_list"):
                    saved_value = available_data.get(destiny_col["name"], [])
                    saved_value.append(value)
                    available_data[destiny_col["name"]] = saved_value
                else:
                    available_data[destiny_col["name"]] = value

        for global_col in self.special_cols["global"]:
            global_value = global_col.get("global_variable")
            available_data[global_col["name"]] = global_value

        for ceil_col in self.special_cols["ceil"]:
            available_data[ceil_col["name"]] = ceil_col["final_value"]

        for tab_col in self.special_cols["tab"]:
            available_data[tab_col["name"]] = self.sheet_name

        for file_name_col in self.special_cols["file_name"]:
            available_data[file_name_col["name"]] = self.file_name_simple

        return available_data

    def basic_available_data(self, available_data, row, field):
        # for field in self.existing_fields:
        field_name = field["name"]
        if field.get("position"):
            value = row[field["position"]]
        else:
            value = available_data.get(field_name)
        if self.not_unicode:
            value = convert_to_str(value)
        # null_to_value = field.get("null_to_value")
        if value is None or value == "":
            null_to_value = get_null_to_value(field)
            if null_to_value:
                value = null_to_value
        delete_text = field.get("delete_text")
        if delete_text:
            strings = delete_text.split(";")
            for string in strings:
                value = re.sub(string, "", value)
        replace_text = field.get("replace_text")
        if replace_text:
            try:
                replacements = replace_text.split(";")
                for replacement in replacements:
                    [old_text, new_text] = replacement.split("-->")
                    old_text = old_text.strip()
                    new_text = new_text.strip()
                    value = value.replace(old_text, new_text)
            except Exception as e:
                raise ValueProcessError(
                    f"No se pudo reemplazar 'parte el texto'", value, str(e))
        same_group_data = field.get("same_group_data")
        copied = False
        if not value and same_group_data and self.last_valid_row:
            value = self.last_valid_row.get(field_name)
            copied = True
            if value and field["data_type"] == "Datetime":
                self.some_date = value
        if not value:
            return value
        if "almost_empty" in field:
            value = None
        elif "text_nulls" in field:
            null_to_value = get_null_to_value(field)
            text_nulls = field["text_nulls"]
            text_nulls = text_nulls.split(",")
            text_nulls = [text_null.strip() for text_null in text_nulls]
            # Si hay que convertir a null y null tiene valor, se vale
            if value in text_nulls:
                value = null_to_value
        if duplicated_in := field.get("duplicated_in"):
            some_almost_empty = False
            has_child = field.get("child")
            # if field.get("clean_function") == "almost_empty":
            if "almost_empty" in field:
                some_almost_empty = True
            if not some_almost_empty and duplicated_in.get("almost_empty"):
                some_almost_empty = True
            if some_almost_empty or has_child:
                pass
            elif not duplicated_in.get("position"):
                error = "No se encontró la posición de la columna duplicada"
                raise ValueProcessError(error, value)
            else:
                duplicated_value = row[duplicated_in["position"]]
                if duplicated_value != value:
                    error = (
                        f"Has clasificado 2 columnas ({field['name_in_data']} "
                        f"y {duplicated_in['name_in_data']}) con la misma "
                        f"variable final '{field['public_name']}',"
                        f"sin embargo sus valores no coinciden")
                    raise ValueProcessError(error, value)
        try:
            if not value:
                pass
            elif copied:
                pass
            elif field["data_type"] == "Datetime":  # and not is_same_date:
                # value = self.get_datetime(format_date, value)
                value = self.date_time(field, value)
                is_delivery = field_name == "date_delivery"
                if not self.some_date or (is_delivery and not same_group_data):
                    self.some_date = value
            elif field["data_type"] == "Integer":
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = int(float(value))
                    except ValueError:
                        error = "No se pudo convertir a número entero"
                        raise ValueProcessError(error, value, "ValueError")
                except TypeError:
                    error = "No se pudo convertir a número entero"
                    raise ValueProcessError(error, value, "TypeError")
                if value < 0:
                    raise ValueProcessError(
                        "El valor no puede ser negativo", value)
            elif field["data_type"] == "Float":
                value = float(value)
            elif field.get("is_list"):
                if not isinstance(value, list):
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        value = [value]
                try:
                    value = [val.strip() for val in value]
                except TypeError:
                    value = [str(value)]
                except Exception as e:
                    error = "No se pudo convertir a lista de valores"
                    raise ValueProcessError(error, value, str(e))
            else:
                value = str(value)
                if self.not_unicode:
                    value = convert_to_str(value)
        except ValueError:
            error = "No se pudo convertir a %s" % field["data_type"]
            raise ValueProcessError(error, value, "ValueError")
        if value:
            regex_format = field.get("regex_format")
            has_own_key = field.get("has_own_key")
            need_check = regex_format and not has_own_key
            if field.get("is_list"):
                for val in value:
                    if need_check and not re.match(regex_format, val):
                        error = f"No pasó validación con el formato de {field_name}"
                        raise ValueProcessError(error, value)
            elif need_check:
                if not re.match(regex_format, value):
                    raise ValueProcessError(
                        f"No se validó con el formato de {field_name}", value)
            elif field.get("max_length"):
                if len(value) > field["max_length"]:
                    raise ValueProcessError(
                        "Hay más caracteres que los permitidos", value)
        return value

    def generic_match(self, cat_name, available_data, is_first=False):
        flat_fields = self.med_cat_flat_fields.get(cat_name, {})
        init_values = self.initial_data.get(cat_name, {})
        initial_all_values = init_values.get("all_values", []).copy()
        initial_data_values = init_values.get("data_values", []).copy()
        all_values = []
        data_values = []
        is_med_unit = cat_name == "medical_unit"
        is_medicament = cat_name == "medicament"
        is_diagnosis = cat_name == "diagnosis"
        own_key_alt = None
        medicament_key = None
        for flat_field in flat_fields:
            field_name = flat_field["name"]
            value = available_data.get(f"{cat_name}_{field_name}", None)
            if is_med_unit or is_medicament:
                is_key = field_name in ["key2", "clues_key"]
                has_own_key = flat_field.get("has_own_key")
                if value and is_key and has_own_key:
                    regex_format = flat_field["regex_format"]
                    if not re.match(regex_format, value):
                        own_key_alt = value
                        all_values.append(None)
                        continue
                is_own = field_name.startswith("own_")
                if not value and own_key_alt and is_own:
                    value = own_key_alt
            if value and is_medicament:
                if field_name == "key2":
                    value = value.replace(".", "")
                    medicament_key = value
                if field_name == "own_key2":
                    initial_all_values[0] = self.provider_id
                    # all_values.insert(0, self.provider_id)
                    if not medicament_key:
                        medicament_key = value
            elif is_med_unit and not value:
                value = flat_field["default_value"]
            if value is not None:
                if is_diagnosis:
                    data_values.append(value)
                else:
                    str_value = value if flat_field["is_string"] else str(value)
                    data_values.append(str_value)
            all_values.append(value)

        if not data_values:
            hash_id = None
        elif is_diagnosis:
            max_len = max(len(values) for values in all_values
                          if values is not None)
            hash_ids = []
            for i in range(max_len):
                diagnosis_values = []
                diagnosis_data_values = []
                for values in all_values:
                    value = values[i] if values and i < len(values) else None
                    diagnosis_values.append(value)
                    if value is not None:
                        diagnosis_data_values.append(value)
                hash_key = self.add_hash_to_cat(
                    diagnosis_values, diagnosis_data_values, cat_name,
                    initial_all_values, is_first)

                hash_ids.append(hash_key)
            hash_id = ";".join(hash_ids)
        else:
            final_data_values = initial_data_values + data_values
            hash_id = self.add_hash_to_cat(
                all_values, final_data_values, cat_name,
                initial_all_values, is_first)
            if medicament_key:
                available_data["medicament_key"] = medicament_key
        available_data[f"{cat_name}_id"] = hash_id
        return available_data

    def add_hash_to_cat(
            self, all_values: list, final_data_values: list,
            cat_name, initial_all_values: list, is_first=False):
        import hashlib

        value_string = "".join(final_data_values)
        value_string = value_string.encode(self.decode_final)
        hash_key = hashlib.md5(value_string).hexdigest()

        if is_first or hash_key not in self.cat_keys[cat_name]:
            every_values = [hash_key] + initial_all_values + all_values
            self.real_buffers.add_cat_row(every_values, cat_name)
            self.cat_keys[cat_name].add(hash_key)
        return hash_key

    def delegation_match(self, available_data):
        if not self.split_by_delegation:
            return None, None
        delegation_name = available_data.get("medical_unit_delegation_name", None)
        delegation_id = None
        delegation_id2 = None
        if delegation_name:
            delegation_name = text_normalizer(delegation_name)
            try:
                delegation_id = self.delegation_cat.get(delegation_name)
            except Exception as e:
                raise NotImplementedError(f"No se encontró la delegación; "
                                          f"{delegation_name} - {e}")
            if "UMAE " in delegation_name:
                delegation_id2 = self.delegation_cat["TODAS LAS UMAES"]
            else:
                delegation_id2 = delegation_id

        return delegation_id, delegation_id2

    def add_missing_row(self, row_data, error=None, drug_id=None):
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
        self.real_buffers.append_missing_row(original_data, error)
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

    def add_missing_field(
            self, row, name_column_id, original_value, error, drug_uuid=None):
        missing_row_id = self.add_missing_row(row, drug_id=drug_uuid)
        if isinstance(original_value, datetime):
            original_value = original_value.strftime("%Y-%m-%d %H:%M:%S")
        missing_field = []
        uuid = str(uuid_lib.uuid4())
        inserted = False
        last_revised = self.last_revised
        # if name_column:
        #     name_column = name_column.id
        self.real_buffers.append_missing_field(
            name_column_id, original_value, error)
        for field in self.model_fields["missing_field"]:
            value = locals().get(field["name"])
            missing_field.append(value)
        self.real_buffers.add_cat_row(missing_field, "missing_field")

    def calculate_iso(self, available_data):
        import hashlib
        try:
            iso_year, iso_week, iso_day = self.some_date.isocalendar()
        except Exception as e:
            raise NotImplementedError(f"Error en fecha; {self.some_date} - {e}")
        year = self.some_date.year
        month = self.some_date.month
        iso_delegation, iso_del2 = self.delegation_match(available_data)

        complex_date = (iso_year, iso_week, iso_del2, year, month)

        variables = ["iso_year", "iso_week", "iso_day", "iso_delegation",
                     "year", "month"]
        for variable in variables:
            available_data[variable] = locals().get(variable)
        # available_data["date_created"] = available_data.get(
        #     "date_release") or available_data.get("date_visit")
        # available_data["date_closed"] = available_data.get("date_delivery")
        folio_document = available_data.get("folio_document")
        if not folio_document:
            raise NotImplementedError("No se encontró folio documento; sin ejemplo")
        if len(folio_document) > 42:
            folio_encoded = folio_document.encode(self.decode_final)
            hash_key = hashlib.md5(folio_encoded).hexdigest()
            folio_document = hash_key[:40]

        folio_ocamis = "|".join([
            str(self.provider_id),
            str(iso_year),
            str(iso_week),
            str(iso_delegation) or '0',
            folio_document])
        if len(folio_ocamis) > 70:
            raise NotImplementedError(f"El folio Ocamis es muy largo; {folio_ocamis}")
        self.months.add((year, month))
        return complex_date, folio_ocamis


def get_null_to_value(field):
    import re
    null_to_value = field.get("null_to_value")
    if null_to_value:
        if null_to_value.startswith("fn("):
            function_name = re.search(r"fn\((.*)\)", null_to_value).group(1)
            if function_name == "imss-resurtibles":
                uuid = str(uuid_lib.uuid4())[:22]
                return f"fn-{uuid}"
            else:
                return None
        else:
            return null_to_value
    else:
        return None


# class DeliveredCalculator:
#
#     def __init__(self, match_class, available_data):
#         self.available_data = available_data
#         self.match_class = match_class
#         self.available_deliveries = match_class.available_deliveries
#         self.global_delivered = match_class.global_delivered
#
#     def get_and_normalize(self, field_name):
#         err = None
#         value = self.available_data.get(field_name)
#         if value:
#             value = text_normalizer(value)
#             if value not in self.available_deliveries:
#                 err = f"Clasificación de surtimiento no contemplada; {value}"
#         return value, err
#
#     def save_error(self, error):
#         delivered = self.available_data.get("delivered_id")
#         if "warning" in error:
#             self.match_class.add_missing_field(
#                 row, classify_id, delivered, error=error,
#                 drug_uuid=uuid)
#         else:
#             self.match_class.add_missing_row(row, error)
#             continue
#
#     def calculate_delivered(self, available_data):
#         import math
#
#         class_med, error1 = self.get_and_normalize("clasif_assortment")
#         class_presc, error2 = self.get_and_normalize("clasif_assortment_presc")
#
#         final_class = class_med or class_presc
#         for error in [error1, error2]:
#             if error:
#                 return available_data, error
#         is_cancelled = final_class == "CANCELADA"
#         prescribed_amount = available_data.get("prescribed_amount")
#         if prescribed_amount is not None:
#             try:
#                 prescribed_amount = int(prescribed_amount)
#             except ValueError:
#                 error = "No se pudo convertir la cantidad prescrita"
#                 return available_data, error
#
#         def identify_errors(av_data, amount, err_text):
#             err = None
#             if amount is None:
#                 if is_cancelled:
#                     av_data["prescribed_amount"] = available_data.get(
#                         "prescribed_amount", 0)
#                     av_data["delivered_amount"] = available_data.get(
#                         "delivered_amount", 0)
#                     av_data["delivered_id"] = "cancelled"
#                 elif self.global_delivered:
#                     pass
#                 elif err_text == "entregada" and class_med or class_presc:
#                     value = None
#                     real_class = self.available_deliveries[final_class]
#                     if real_class in ['cancelled', 'denied']:
#                         value = 0
#                     elif real_class == 'complete':
#                         value = prescribed_amount
#                     elif real_class == 'partial':
#                         if class_med:
#                             value = int(math.floor(prescribed_amount / 2))
#                         else:
#                             value = prescribed_amount
#                             real_class = 'forced_partial'
#                     if value is not None:
#                         av_data["delivered_amount"] = value
#                         av_data["delivered_id"] = real_class
#                     else:
#                         err = f"No se puede determinar el status de entrega; " \
#                                 f"No encontramos la cantidad {err_text}"
#                 else:
#                     err = f"No se puede determinar el status de entrega; " \
#                           f"No encontramos la cantidad {err_text}"
#             elif amount > 30000:
#                 err = f"Existe una cantidad inusualmente alta; cantidad {err_text}"
#             elif amount < 0:
#                 err = f"Existe una cantidad negativa; cantidad {err_text}"
#             return av_data, err
#
#         available_data, error = identify_errors(
#             available_data, prescribed_amount, "prescrita")
#
#         if error or available_data.get("delivered_id"):
#             return available_data, error
#
#         delivered_amount = available_data.get("delivered_amount")
#
#         if delivered_amount is None:
#             not_delivered_amount = available_data.get("not_delivered_amount", None)
#             if not_delivered_amount is not None:
#                 try:
#                     not_delivered_amount = int(not_delivered_amount)
#                 except ValueError:
#                     error = (f"No se pudo convertir la cantidad no entregada; "
#                              f"{not_delivered_amount}")
#                     return available_data, error
#                 delivered_amount = prescribed_amount - not_delivered_amount
#                 available_data["delivered_amount"] = delivered_amount
#         else:
#             try:
#                 delivered_amount = int(delivered_amount)
#             except ValueError:
#                 error = (f"No se pudo convertir la cantidad entregada; "
#                          f"{delivered_amount}")
#                 return available_data, error
#
#         available_data, error = identify_errors(
#             available_data, delivered_amount, "entregada")
#         if error or available_data.get("delivered_id"):
#             return available_data, error
#         if self.global_delivered:
#             available_data["delivered_id"] = self.global_delivered
#             return available_data, None
#         if prescribed_amount == delivered_amount:
#             if is_cancelled:
#                 delivered = "cancelled"
#             elif prescribed_amount == 0:
#                 delivered = "zero"
#             else:
#                 delivered = "complete"
#         elif not delivered_amount:
#             if is_cancelled:
#                 delivered = "cancelled"
#             else:
#                 delivered = "denied"
#         elif delivered_amount < prescribed_amount:
#             delivered = "partial"
#         elif delivered_amount > prescribed_amount:
#             delivered = "over_delivered"
#         elif is_cancelled:
#             delivered = "cancelled"
#         else:
#             return available_data, "No se puede determinar el status de entrega"
#
#         if prescribed_amount > 30:
#             if delivered == "denied":
#                 delivered = "big_denied"
#             elif delivered == "partial":
#                 delivered = "big_partial"
#
#         available_data["delivered_id"] = delivered
#         if class_med:
#             if delivered != self.available_deliveries[class_med]:
#                 error = (f"warning: El status escrito '{class_med}' no"
#                          f" coincide con el status calculado: '{delivered}'")
#                 return available_data, error
#         return available_data, None
