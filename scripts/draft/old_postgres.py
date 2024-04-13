constraints = {
    "formula_drug": [
        "pkey",
        "prescribed_amount_check",
        "delivered_amount_check",
        "row_seq_check",
        "prescription_id_cdf044b3_fk_formula_p",
        "container_id_902ff1c3_fk_desabasto_container_id",
        "data_file_id_e47b8ac0_fk_inai_datafile_id",
        "delivered_id_ff5c08d9_fk_formula_d",
    ],
    "formula_prescription": [
        "pkey",
        "iso_year_check",
        "iso_week_check",
        "iso_day_check",
        "area_id_70b37bf9_fk_catalog_area_id",
        "clues_id_7b015cda_fk_desabasto_clues_id",
        "doctor_id_6f41a184_fk_formula_doctor_uuid",
        "month_check",
        "delegation_id_0b8cad2e_fk_catalog_d",
        "delivered_final_id_331bd9fa_fk_formula_d",
    ],
    "formula_missingrow": [
        "drug_id_746af424_fk_formula_drug_uuid"
        "prescription_id_f6fbc500_fk_formula_p"
    ]
}

indexes = {
    "formula_drug": [
        "container_id_902ff1c3",
        "data_file_id_e47b8ac0",
        "delivered_id_ff5c08d9",
        "delivered_id_ff5c08d9_like",
        "prescription_id_cdf044b3",
    ],
    "formula_prescription": [
        "area_id_70b37bf9",
        "clues_id_7b015cda",
        "delegation_id_0b8cad2e",
        "delivered_id_8c182a3e",
        "delivered_id_8c182a3e_like",
        "doctor_id_6f41a184"
    ],
}


def recreate_index_with_name(name):
    from django.db import connection
    cursor = connection.cursor()
    split_name = name.split("_")[0]
    table_name = f"{split_name[0]}_{split_name[1]}"
    field_name = f"{split_name[2]}_id"
    sql_query = f"""
        CREATE INDEX {name} ON {table_name} USING btree ({field_name})
    """
    # CREATE INDEX {name} ON formula_prescription (doctor_id);

    cursor.execute(sql_query)
    cursor.close()
    connection.close()
