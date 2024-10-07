import csv
import io
from scripts.common import build_s3
from task.aws.common import BotoUtils


def imss_join(wr_id):
    from inai.models import WeekRecord

    final_path = f"nacional/imss (ordinario)/join/semana_{wr_id}.csv"
    s3 = build_s3()
    s3_utils = BotoUtils(s3)

    final_csv = io.StringIO()
    buffer = csv.writer(final_csv, delimiter="|")

    week_record = WeekRecord.objects.get(id=wr_id)
    data_files = week_record.table_files.filter(collection__isnull=True)
    header_ready = False
    for table_file in data_files:
        # print("table_file.file.name", table_file.file.name)
        table_csv = s3_utils.get_object_csv(table_file.file.name)
        # print("table_csv", table_csv)
        for idx_row, row in enumerate(table_csv):
            if idx_row == 0:
                if header_ready:
                    continue
                buffer.writerow(row)
                header_ready = True
                continue
            buffer.writerow(row)
    s3_utils.save_file_in_aws(final_csv.getvalue(), final_path)


fields = [
    "uuid",
    "rx_id",
    "sheet_file_id",
    "row_seq",
    "lap_sheet_id",
    "medicament_id",
    "prescribed_amount",
    "delivered_amount",
    "delivered_id",
    "date_created",
    "date_closed",
    "price",
    "entity_week_id",
    "uuid_folio",
    "entity_id",
    "folio_ocamis",
    "folio_document",
    "year",
    "month",
    "iso_year",
    "iso_week",
    "iso_day",
    "iso_delegation",
    "medical_unit_id",
    "area_id",
    "delivered_final_id",
    "document_type",
    "date_release",
    "date_visit",
    "date_delivery",
    "doctor_id",
    "diagnosis_id"]


def build_medicaments_dict():
    from med_cat.models import Medicament
    final_dict = {}
    all_medicaments = Medicament.objects\
        .filter(own_key2__isnull=False)\
        .values_list("hex_hash", "own_key2")
    for hex_hash, own_key2 in all_medicaments:
        final_dict[hex_hash] = own_key2
    return final_dict


def imss_compare(wr_id=34):
    from scripts.common import build_s3
    base_path = "nacional/imss (ordinario)/join"
    s3 = build_s3()
    s3_utils = BotoUtils(s3)
    origins = {
        "init": {
            "path": f"{base_path}/semana_{wr_id}.csv",
            "data": {}, "has_medicament_key": False},
        "stock": {
            "path": f"{base_path}/campeche_farmacia.csv",
            "data": {}, "has_medicament_key": True},
        "rx": {"path": f"{base_path}/campeche_recetas.csv",
               "data": {}, "has_medicament_key": True},
    }
    medicaments_dict = build_medicaments_dict()
    unique_keys = set()
    for key, origin in origins.items():
        has_medicament_key = origin["has_medicament_key"]
        csv_data = s3_utils.get_object_csv(origin["path"])
        headers = None
        for idx, row in enumerate(csv_data):
            if idx == 0:
                headers = row
                continue
            row_dict = dict(zip(headers, row))
            if not has_medicament_key:
                med_value = medicaments_dict.get(row[5])
                row_dict["medicament_key"] = med_value
            key = f"{row_dict['folio_document']}:{row_dict['medicament_key']}"
            unique_keys.add(key)
            origin["data"][key] = row_dict

    final_name = f"nacional/imss (ordinario)/join/semana_{wr_id}_compare.csv"
    new_csv = io.StringIO()
    buffer = csv.writer(new_csv, delimiter="|")
    headers = ["folio_document", "medicament_key"]
    common_fields = [
        "prescribed_amount", "delivered_amount", "delivered_id",
        "document_type", "date_release", "date_visit"]
    for origin in origins.keys():
        for field in common_fields:
            headers.append(f"{origin}:{field}")

    buffer.writerow(headers)
    sorted_keys = sorted(unique_keys)

    for key in sorted_keys:
        folio_document, medicament_key = key.split(":")
        row = [folio_document, medicament_key]
        for origin in origins.keys():
            data = origins[origin]["data"].get(key, {})
            for field in common_fields:
                row.append(data.get(field, ""))
        buffer.writerow(row)

    s3_utils.save_file_in_aws(new_csv.getvalue(), final_name)



