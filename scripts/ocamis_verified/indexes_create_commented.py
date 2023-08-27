# together 1000 --> 34 minutos, 43%
f"""
alter table formula_rx
    add constraint formula_rx_pkey
    primary key (uuid_folio),
add constraint formula_rx_delivered_final_id_331bd9fa_fk_med_cat_d
    foreign key (delivered_final_id) references med_cat_delivered
    deferrable initially deferred,
add constraint formula_rx_entity_id_d8660a11_fk_geo_entity_id
    foreign key (entity_id) references geo_entity
    deferrable initially deferred;
"""

create_constraints = [
    # BÁSICOS
    # 22 minutos, 22%
    # 1000 Storage -> 18 minutos, 22%
    # 500 Storage ->
    "alter table formula_rx\n    add constraint formula_rx_pkey\n    primary key (uuid_folio);",

    # 32 minutos, 36%
    "alter table formula_drug\n    add constraint formula_drug_pkey\n    primary key (uuid);",

    # INDISPENSABLES:
    # 28 minutos, 35%
    "create index if not exists formula_drug_rx_id_cdf044b3\n    on formula_drug (rx_id);",
    # 44 minutos, 35%
    "alter table formula_drug\n    add constraint formula_drug_rx_id_cdf044b3_fk_formula_p\n    foreign key (rx_id) references formula_rx\n    deferrable initially deferred;",

    "create index if not exists formula_drug_delivered_id_ff5c08d9\n    on formula_drug (delivered_id);",
    "alter table formula_drug\n    add constraint formula_drug_delivered_id_ff5c08d9_fk_med_cat_d\n    foreign key (delivered_id) references med_cat_delivered\n    deferrable initially deferred;",
    # 1000 Storage (después de abajo)  -> 13 minutos, 18%
    "create index if not exists formula_rx_delivered_final_id_331bd9fa\n    on formula_rx (delivered_final_id);",
    # 1000 Storage (sin indexar) -> 8 minutos, 9%
    "alter table formula_rx\n    add constraint formula_rx_delivered_final_id_331bd9fa_fk_med_cat_d\n    foreign key (delivered_final_id) references med_cat_delivered\n    deferrable initially deferred;",

    # 1000 Storage (antes de abajo) -> 9 minutos, 16%
    "create index if not exists formula_rx_entity_id_d8660a11\n    on formula_rx (entity_id);",
    # 1000 Storage (después de indexar) -> 7 minutos, 10%
    "alter table formula_rx\n    add constraint formula_rx_entity_id_d8660a11_fk_geo_entity_id\n    foreign key (entity_id) references geo_entity\n    deferrable initially deferred;",

    "create index if not exists formula_drug_medicament_id_630af6c3\n    on formula_drug (medicament_id);",
    "alter table formula_drug\n    add constraint formula_drug_medicament_id_630af6c3_fk_med_cat_m\n    foreign key (medicament_id) references med_cat_medicament\n    deferrable initially deferred;",

    # IMPORTANTES
    # 500 Storage -> 28 minutos, 25%
    "create index if not exists formula_rx_medical_unit_id_27e254eb\n    on formula_rx (medical_unit_id);",
    # 500 Storage -> 8 minutos, 9%
    "alter table formula_rx\n    add constraint formula_rx_medical_unit_id_27e254eb_fk_med_c_liat_m\n    foreign key (medical_unit_id) references med_cat_medicalunit\n    deferrable initially deferred;",
    "create index if not exists formula_rx_doctor_id_6f41a184\n    on formula_rx (doctor_id);",
    "alter table formula_rx\n    add constraint formula_rx_doctor_id_6f41a184_fk_med_cat_d\n    foreign key (doctor_id) references med_cat_doctor\n    deferrable initially deferred;",

    # POCO IMPORTANTES:
    "create index if not exists formula_rx_diagnosis_id_c4040beb\n    on formula_rx (diagnosis_id);",
    "alter table formula_rx\n    add constraint formula_rx_diagnosis_id_c4040beb_fk_med_cat_d\n    foreign key (diagnosis_id) references med_cat_diagnosis\n    deferrable initially deferred;",
    "create index if not exists formula_rx_area_id_70b37bf9\n    on formula_rx (area_id);",
    "alter table formula_rx\n    add constraint formula_rx_area_id_70b37bf9_fk_med_cat_area_hex_hash\n    foreign key (area_id) references med_cat_area\n    deferrable initially deferred;",

    # NO INDISPENSABLES:
    "create index if not exists formula_drug_lap_sheet_id_65587308\n    on formula_drug (lap_sheet_id);",
    "alter table formula_drug\n    add constraint formula_drug_lap_sheet_id_65587308_fk_inai_lapsheet_id\n    foreign key (lap_sheet_id) references inai_lapsheet\n    deferrable initially deferred;",
    "create index if not exists formula_drug_sheet_file_id_568cdddf\n    on formula_drug (sheet_file_id);",
    "alter table formula_drug\n    add constraint formula_drug_sheet_file_id_568cdddf_fk_inai_sheetfile_id\n    foreign key (sheet_file_id) references inai_sheetfile\n    deferrable initially deferred;",

    # INNECESARIOS
    "alter table formula_rx\n    add constraint formula_rx_iso_year_check\n    check (iso_year >= 0);",
    "alter table formula_rx\n    add constraint formula_rx_month_check\n    check (month >= 0);",
    "alter table formula_rx\n    add constraint formula_rx_iso_week_check\n    check (iso_week >= 0);",
    "alter table formula_rx\n    add constraint formula_rx_iso_day_check\n    check (iso_day >= 0);",
    "alter table formula_rx\n    add constraint formula_rx_year_check\n    check (year >= 0);",
    "alter table formula_rx\n    add constraint formula_rx_iso_delegation_check\n    check (iso_delegation >= 0);",
    # Iba en 7 minutos, probablemente sea lo mismo
    "alter table formula_drug\n    add constraint formula_drug_delivered_amount_check\n    check (delivered_amount >= 0);",
    "alter table formula_drug\n    add constraint formula_drug_row_seq_check\n    check (row_seq >= 0);",
    "alter table formula_drug\n    add constraint formula_drug_prescribed_amount_check\n    check (prescribed_amount >= 0);",

    # NO ESTÁ CLARA SU UTILIDAD
    "create index if not exists formula_rx_doctor_id_6f41a184_like\n    on formula_rx (doctor_id varchar_pattern_ops);",
    "create index if not exists formula_drug_delivered_id_ff5c08d9_like\n    on formula_drug (delivered_id varchar_pattern_ops);",
    "create index if not exists formula_rx_delivered_final_id_331bd9fa_like\n    on formula_rx (delivered_final_id varchar_pattern_ops);",
    "create index if not exists formula_rx_area_id_70b37bf9_like\n    on formula_rx (area_id varchar_pattern_ops);",
    "create index if not exists formula_rx_diagnosis_id_c4040beb_like\n    on formula_rx (diagnosis_id varchar_pattern_ops);",
    "create index if not exists formula_rx_medical_unit_id_27e254eb_like\n    on formula_rx (medical_unit_id varchar_pattern_ops);",
    "create index if not exists formula_drug_medicament_id_630af6c3_like\n    on formula_drug (medicament_id varchar_pattern_ops);",

    # CADUCOS
    "alter table formula_documenttype\n    add constraint formula_documenttype_pkey\n    primary key (name);",
    "create index if not exists formula_documenttype_name_ebbaa6b4_like\n    on formula_documenttype (name varchar_pattern_ops);",
    "alter table formula_medicalspeciality\n    add constraint formula_medicalspeciality_pkey\n    primary key (id);"
]

simples = f"""
alter table formula_missingfield
add constraint formula_missingfield_pkey
primary key (uuid);

alter table formula_missingrow
add constraint formula_missingrow_pkey
primary key (uuid);

create index if not exists formula_missingrow_sheet_file_id_e5292867
on formula_missingrow (sheet_file_id);

alter table formula_missingrow
add constraint formula_missingrow_sheet_file_id_e5292867_fk_inai_sheetfile_id
foreign key (sheet_file_id) references inai_sheetfile
deferrable initially deferred;

create index if not exists formula_missingfield_name_column_id_d2bc6a65
on formula_missingfield (name_column_id);

alter table formula_missingfield
add constraint formula_missingfield_name_column_id_d2bc6a65_fk_data_para
foreign key (name_column_id) references data_param_namecolumn
deferrable initially deferred;

create index if not exists formula_missingfield_missing_row_id_8903ee88
on formula_missingfield (missing_row_id);

alter table formula_missingfield
add constraint formula_missingfield_missing_row_id_8903ee88_fk_formula_m
foreign key (missing_row_id) references formula_missingrow
deferrable initially deferred;

create index if not exists formula_missingrow_drug_id_746af424
on formula_missingrow (drug_id);

alter table formula_missingrow
add constraint formula_missingrow_drug_id_746af424_fk_formula_drug_uuid
foreign key (drug_id) references formula_drug
deferrable initially deferred;
"""
