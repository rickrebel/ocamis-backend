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

new_operations = [
    {
        "script": "alter table formula_rx\n"
                  "    add constraint formula_rx_pkey\n"
                  "    primary key (uuid_folio);",
        "drop_script": "alter table formula_rx drop constraint if exists formula_rx_pkey;",
        "order": 1,
        "collection": "Rx",
        "operation_type": "constraint",
        "comment": "BÁSICOS \n22 minutos, 22%",
    },
    {
        "script": "alter table formula_drug\n"
                  "    add constraint formula_drug_pkey\n"
                  "    primary key (uuid);",
        "drop_script": "alter table formula_drug drop constraint if exists formula_drug_pkey;",
        "order": 2,
        "collection": "Drug",
        "operation_type": "constraint",
        "comment": "BÁSICOS \n32 minutos, 36%"
    },
    {
        "script": "alter table formula_complementrx \n"
                  "     add constraint formula_complementrx_pkey \n"
                  "     primary key (uuid_comp_rx)",
        "drop_script": "alter table formula_complementrx drop constraint if exists formula_complementrx_pkey;",
        "order": 3,
        "collection": "ComplementRx",
        "operation_type": "constraint",
        "comment": "BÁSICOS"
    },
    {
        "script": "alter table formula_complementdrug  \n"
                  " add constraint formula_complementdrug_pkey \n"
                  " primary key (uuid_comp_drug)",
        "drop_script": "alter table formula_complementdrug drop constraint if exists formula_complementdrug_pkey;",
        "order": 4,
        "collection": "ComplementDrug",
        "operation_type": "constraint",
        "comment": "BÁSICOS"
    },
    {
        "script": "alter table formula_diagnosisrx \n"
                  " add constraint diagnosis_rx_pkey \n"
                  " primary key (uuid_diag_rx)",
        "drop_script": "alter table formula_diagnosisrx drop constraint if exists diagnosis_rx_pkey;",
        "order": 5,
        "collection": "DiagnosisRx",
        "operation_type": "constraint",
        "comment": "BÁSICOS"
    },
    {
        "script": "create index if not exists formula_drug_rx_id_cdf044b3\n"
                  "    on formula_drug (rx_id);",
        "drop_script": "drop index if exists formula_drug_rx_id_cdf044b3;",
        "order": 10,
        "collection": "Drug",
        "operation_type": "index",
        "comment": "INDISPENSABLES \n28 minutos, 35%"
    },
    {
        "script": "alter table formula_drug\n"
                  "    add constraint formula_drug_rx_id_cdf044b3_fk_formula_p\n"
                  "    foreign key (rx_id) references formula_rx"
                  "    deferrable initially deferred;",
        "drop_script": "alter table formula_drug drop constraint if exists formula_drug_rx_id_cdf044b3_fk_formula_p;",
        "order": 11,
        "collection": "Drug",
        "operation_type": "constraint",
        "comment": "INDISPENSABLES \n44 minutos, 35%"
    },
    {
        "script": "create index if not exists formula_drug_delivered_id_ff5c08d9\n"
                  "    on formula_drug (delivered_id);",
        "drop_script": "drop index if exists formula_drug_delivered_id_ff5c08d9;",
        "order": 12,
        "collection": "Drug",
        "operation_type": "index",
        "comment": "INDISPENSABLES"
    },
    {
        "script": "alter table formula_drug\n"
                  "    add constraint formula_drug_delivered_id_ff5c08d9_fk_med_cat_d\n"
                  "    foreign key (delivered_id) references med_cat_delivered\n"
                  "    deferrable initially deferred;",
        "drop_script": "alter table formula_drug drop constraint if exists formula_drug_delivered_id_ff5c08d9_fk_med_cat_d;",
        "order": 13,
        "collection": "Drug",
        "operation_type": "constraint",
        "comment": "INDISPENSABLES"
    },
    {
        "script": "create index if not exists formula_rx_delivered_final_id_331bd9fa\n"
                  "    on formula_rx (delivered_final_id);",
        "drop_script": "drop index if exists formula_rx_delivered_final_id_331bd9fa;",
        "order": 14,
        "collection": "Rx",
        "operation_type": "index",
        "comment": "INDISPENSABLES \n13 minutos, 18%"
    },
    {
        "script": "alter table formula_rx\n"
                  "    add constraint formula_rx_delivered_final_id_331bd9fa_fk_med_cat_d\n"
                  "    foreign key (delivered_final_id) references med_cat_delivered"
                  "    deferrable initially deferred;",
        "drop_script": "alter table formula_rx drop constraint if exists formula_rx_delivered_final_id_331bd9fa_fk_med_cat_d;",
        "order": 15,
        "collection": "Rx",
        "operation_type": "constraint",
        "comment": "INDISPENSABLES \n8 minutos, 9%"
    },
    {
        "script": "create index if not exists formula_rx_provider_id_d8660a11\n"
                  "    on formula_rx (provider_id);",
        "drop_script": "drop index if exists formula_rx_provider_id_d8660a11;",
        "order": 16,
        "collection": "Rx",
        "operation_type": "index",
        "comment": "INDISPENSABLES\n 9 minutos, 16%"
    },
    {
        "script": "alter table formula_rx\n"
                  "    add constraint formula_rx_provider_id_d8660a11_fk_geo_provider_id\n"
                  "    foreign key (provider_id) references geo_entity\n"
                  "    deferrable initially deferred;",
        "drop_script": "alter table formula_rx drop constraint if exists formula_rx_provider_id_d8660a11_fk_geo_provider_id;",
        "order": 17,
        "collection": "Rx",
        "operation_type": "constraint",
        "comment": "INDISPENSABLES \n 7 minutos, 10%"
    },
    {
        "script": "create index if not exists formula_drug_medicament_id_630af6c3\n"
                  "    on formula_drug (medicament_id);",
        "drop_script": "drop index if exists formula_drug_medicament_id_630af6c3;",
        "order": 18,
        "collection": "Drug",
        "operation_type": "index",
        "comment": "INDISPENSABLES"
    },
    {
        "script": "alter table formula_drug\n"
                  "    add constraint formula_drug_medicament_id_630af6c3_fk_med_cat_m\n"
                  "    foreign key (medicament_id) references med_cat_medicament\n"
                  "    deferrable initially deferred;",
        "drop_script": "alter table formula_drug drop constraint if exists formula_drug_medicament_id_630af6c3_fk_med_cat_m;",
        "order": 19,
        "collection": "Drug",
        "operation_type": "constraint",
        "comment": "INDISPENSABLES"
    },
    # "create index if not exists formula_diagnosisrx_rx_id_62aa4c2f\n    on formula_diagnosisrx (rx_id);",
    {
        "script": "create index if not exists formula_diagnosisrx_rx_id_62aa4c2f\n"
                  "    on formula_diagnosisrx (rx_id);",
        "drop_script": "drop index if exists formula_diagnosisrx_rx_id_62aa4c2f;",
        "order": 20,
        "collection": "DiagnosisRx",
        "operation_type": "index",
        "comment": "INDISPENSABLES"
    },
    {
        "script": "alter table formula_diagnosisrx \n"
                    " add constraint formula_diagnosisrx_rx_id_62aa4c2f_fk_formula_rx_uuid_folio\n"
                    " foreign key (rx_id) references formula_rx\n"
                    " deferrable initially deferred;",
        "drop_script": "alter table formula_diagnosisrx drop constraint if exists formula_diagnosisrx_rx_id_62aa4c2f_fk_formula_rx_uuid_folio;",
        "order": 21,
        "collection": "DiagnosisRx",
        "operation_type": "constraint",
        "comment": "INDISPENSABLES"
    },
    {
        "script": "create index if not exists formula_complementrx_rx_id_02b25250\n"
                  "    on formula_complementrx (rx_id);",
        "drop_script": "drop index if exists formula_complementrx_rx_id_02b25250;",
        "order": 21,
        "collection": "ComplementRx",
        "operation_type": "index",
        "comment": "INDISPENSABLES"
    },
    {
        "script": "alter table formula_complementrx  \n \n"
                  "add constraint formula_complementrx_rx_id_02b25250_fk_formula_rx_uuid_folio\n"
                  "   foreign key (rx_id) references formula_rx\n"
                  "            deferrable initially deferred;",
        "drop_script": "alter table formula_complementrx drop constraint if exists formula_complementrx_rx_id_02b25250_fk_formula_rx_uuid_folio;",
        "order": 22,
        "collection": "ComplementRx",
        "operation_type": "constraint",
        "comment": "INDISPENSABLES"
    },
    {
        "script": "create index if not exists formula_complementdrug_drug_id_9274b9d5\n"
                  "    on formula_complementdrug (drug_id);",
        "drop_script": "drop index if exists formula_complementdrug_drug_id_9274b9d5;",
        "order": 23,
        "collection": "ComplementDrug",
        "operation_type": "index",
        "comment": "INDISPENSABLES"
    },
    {
        "script": "alter table formula_complementdrug  \n \n"
                  "add constraint formula_complementdrug_drug_id_9274b9d5_fk_formula_drug_uuid\n"
                  "   foreign key (drug_id) references formula_drug\n"
                  "            deferrable initially deferred;",
        "drop_script": "alter table formula_complementdrug drop constraint if exists formula_complementdrug_drug_id_9274b9d5_fk_formula_drug_uuid;",
        "order": 24,
        "collection": "ComplementDrug",
        "operation_type": "constraint",
        "comment": "INDISPENSABLES"
    },
    {
        "script": "create index if not exists formula_rx_medical_unit_id_27e254eb\n"
                  "    on formula_rx (medical_unit_id);",
        "drop_script": "drop index if exists formula_rx_medical_unit_id_27e254eb;",
        "order": 30,
        "collection": "Rx",
        "operation_type": "index",
        "comment": "IMPORTANTES\n 28 minutos, 25%"
    },
    {
        "script": "alter table formula_rx\n"
                  "    add constraint formula_rx_medical_unit_id_27e254eb_fk_med_c_liat_m\n"
                  "    foreign key (medical_unit_id) references med_cat_medicalunit\n"
                  "    deferrable initially deferred;",
        "drop_script": "alter table formula_rx drop constraint if exists formula_rx_medical_unit_id_27e254eb_fk_med_c_liat_m;",
        "order": 31,
        "collection": "Rx",
        "operation_type": "constraint",
        "comment": "IMPORTANTES \n 8 minutos, 9%"
    },
    {
        "script": "create index if not exists formula_rx_doctor_id_6f41a184\n"
                  "    on formula_rx (doctor_id);",
        "drop_script": "drop index if exists formula_rx_doctor_id_6f41a184;",
        "order": 32,
        "collection": "Rx",
        "operation_type": "index",
        "comment": "IMPORTANTES"
    },
    {
        "script": "alter table formula_rx\n"
                  "    add constraint formula_rx_doctor_id_6f41a184_fk_med_cat_d\n"
                  "    foreign key (doctor_id) references med_cat_doctor"
                  "    deferrable initially deferred;",
        "drop_script": "alter table formula_rx drop constraint if exists formula_rx_doctor_id_6f41a184_fk_med_cat_d;",
        "order": 33,
        "collection": "Rx",
        "operation_type": "constraint",
        "comment": "IMPORTANTES"
    },
    {
        "script": "create index if not exists formula_complementrx_area_id_b0ff963e\n"
                  "    on formula_complementrx (area_id);",
        "drop_script": "drop index if exists formula_complementrx_area_id_b0ff963e;",
        "order": 60,
        "collection": "ComplementRx",
        "operation_type": "index",
        "comment": "POCO IMPORTANTES"
    },
    {
        "script": "alter table formula_complementrx\n"
                  "    add constraint formula_complementrx_area_id_b0ff963e_fk_med_cat_area_hex_hash\n"
                  "    foreign key (area_id) references med_cat_area\n"
                  "    deferrable initially deferred;",
        "drop_script": "alter table formula_complementrx drop constraint if exists formula_complementrx_area_id_b0ff963e_fk_med_cat_area_hex_hash;",
        "order": 61,
        "collection": "ComplementRx",
        "operation_type": "constraint",
        "comment": "POCO IMPORTANTES"
    },
    {
        "script": "create index if not exists formula_diagnosisrx_diagnosis_id_efb405f2\n"
                  "    on formula_diagnosisrx (diagnosis_id);",
        "drop_script": "drop index if exists formula_diagnosisrx_diagnosis_id_efb405f2;",
        "order": 62,
        "collection": "ComplementRx",
        "operation_type": "index",
        "comment": "POCO IMPORTANTES"
    },
    {
        "script": "alter table formula_diagnosisrx \n"
                  " add constraint formula_diagnosisrx_diagnosis_id_efb405f2_fk_med_cat_d\n"
                  " foreign key (diagnosis_id) references med_cat_diagnosis\n"
                  " deferrable initially deferred",
        "drop_script": "alter table formula_diagnosisrx drop constraint if exists formula_diagnosisrx_diagnosis_id_efb405f2_fk_med_cat_d;",
        "order": 64,
        "collection": "DiagnosisRx",
        "operation_type": "constraint",
        "comment": "POCO IMPORTANTES"
    },
    {
        "script": "create index if not exists formula_drug_lap_sheet_id_65587308\n"
                  "    on formula_drug (lap_sheet_id);",
        "drop_script": "drop index if exists formula_drug_lap_sheet_id_65587308;",
        "order": 70,
        "collection": "Drug",
        "operation_type": "index",
        "comment": "NO INDISPENSABLES"
    },
    {
        "script": "alter table formula_drug\n"
                  "    add constraint formula_drug_lap_sheet_id_65587308_fk_inai_lapsheet_id\n"
                  "    foreign key (lap_sheet_id) references inai_lapsheet\n"
                  "    deferrable initially deferred;",
        "drop_script": "alter table formula_drug drop constraint if exists formula_drug_lap_sheet_id_65587308_fk_inai_lapsheet_id;",
        "order": 71,
        "collection": "Drug",
        "operation_type": "constraint",
        "comment": "NO INDISPENSABLES"
    },
    {
        "script": "create index if not exists formula_drug_sheet_file_id_568cdddf\n"
                  "    on formula_drug (sheet_file_id);",
        "drop_script": "drop index if exists formula_drug_sheet_file_id_568cdddf;",
        "order": 72,
        "collection": "Drug",
        "operation_type": "index",
        "comment": "NO INDISPENSABLES"
    },
    {
        "script": "alter table formula_drug\n"
                  "    add constraint formula_drug_sheet_file_id_568cdddf_fk_inai_sheetfile_id\n"
                  "    foreign key (sheet_file_id) references inai_sheetfile\n"
                  "    deferrable initially deferred;",
        "drop_script": "alter table formula_drug drop constraint if exists formula_drug_sheet_file_id_568cdddf_fk_inai_sheetfile_id;",
        "order": 73,
        "collection": "Drug",
        "operation_type": "constraint",
        "comment": "NO INDISPENSABLES"
    },
    {
        "script": "alter table formula_rx\n"
                  "    add constraint formula_rx_iso_year_check\n"
                  "    check (iso_year >= 0);",
        "drop_script": "alter table formula_rx drop constraint if exists formula_rx_iso_year_check;",
        "order": 100,
        "collection": "Rx",
        "operation_type": "constraint",
        "comment": "INNECESARIOS"
    },
    {
        "script": "alter table formula_rx\n"
                  "    add constraint formula_rx_month_check\n"
                  "    check (month >= 0);",
        "drop_script": "alter table formula_rx drop constraint if exists formula_rx_month_check;",
        "order": 101,
        "collection": "Rx",
        "operation_type": "constraint",
        "comment": "INNECESARIOS"
    },
    {
        "script": "alter table formula_rx\n"
                  "    add constraint formula_rx_iso_week_check\n"
                  "    check (iso_week >= 0);",
        "drop_script": "alter table formula_rx drop constraint if exists formula_rx_iso_week_check;",
        "order": 102,
        "collection": "Rx",
        "operation_type": "constraint",
        "comment": "INNECESARIOS"
    },
    {
        "script": "alter table formula_rx\n"
                  "    add constraint formula_rx_iso_day_check\n"
                  "    check (iso_day >= 0);",
        "drop_script": "alter table formula_rx drop constraint if exists formula_rx_iso_day_check;",
        "order": 103,
        "collection": "Rx",
        "operation_type": "constraint",
        "comment": "INNECESARIOS"
    },
    {
        "script": "alter table formula_rx\n"
                  "    add constraint formula_rx_year_check\n"
                  "    check (year >= 0);",
        "drop_script": "alter table formula_rx drop constraint if exists formula_rx_year_check;",
        "order": 104,
        "collection": "Rx",
        "operation_type": "constraint",
        "comment": "INNECESARIOS"
    },
    {
        "script": "alter table formula_rx\n"
                  "    add constraint formula_rx_iso_delegation_check\n"
                  "    check (iso_delegation >= 0);",
        "drop_script": "alter table formula_rx drop constraint if exists formula_rx_iso_delegation_check;",
        "order": 105,
        "collection": "Rx",
        "operation_type": "constraint",
        "comment": "INNECESARIOS"
    },
    {
        "script": "alter table formula_drug\n"
                  "    add constraint formula_drug_delivered_amount_check\n"
                  "    check (delivered_amount >= 0);",
        "drop_script": "alter table formula_drug drop constraint if exists formula_drug_delivered_amount_check;",
        "order": 106,
        "collection": "Drug",
        "operation_type": "constraint",
        "comment": "INNECESARIOS"
    },
    {
        "script": "alter table formula_drug\n"
                  "    add constraint formula_drug_row_seq_check\n"
                  "    check (row_seq >= 0);",
        "drop_script": "alter table formula_drug drop constraint if exists formula_drug_row_seq_check;",
        "order": 107,
        "collection": "Drug",
        "operation_type": "constraint",
        "comment": "INNECESARIOS"
    },
    {
        "script": "alter table formula_drug\n"
                  "    add constraint formula_drug_prescribed_amount_check\n"
                  "    check (prescribed_amount >= 0);",
        "drop_script": "alter table formula_drug drop constraint if exists formula_drug_prescribed_amount_check;",
        "order": 108,
        "collection": "Drug",
        "operation_type": "constraint",
        "comment": "INNECESARIOS"
    },
    {
        "script": "alter table formula_drug\n"
                  "    add constraint formula_rx_days_between_check\n"
                  "    check (days_between >= 0);",
        "drop_script": "alter table formula_drug drop constraint if exists formula_rx_days_between_check;",
        "order": 109,
        "collection": "Rx",
        "operation_type": "constraint",
        "comment": "INNECESARIOS"
    },
    {
        "script": "alter table formula_complementrx  \n \n"
                  "add constraint formula_complementrx_age_check\n"
                  "            check (age >= 0)",
        "drop_script": "alter table formula_complementrx drop constraint if exists formula_complementrx_age_check;",
        "order": 110,
        "collection": "ComplementRx",
        "operation_type": "constraint",
        "comment": "INNECESARIOS"
    },
    {
        "script": "create index if not exists formula_rx_doctor_id_6f41a184_like\n"
                  "    on formula_rx (doctor_id varchar_pattern_ops);",
        "drop_script": "drop index if exists formula_rx_doctor_id_6f41a184_like;",
        "order": 90,
        "collection": "Rx",
        "operation_type": "index",
        "comment": "NO ESTÁ CLARA SU UTILIDAD"
    },
    {
        "script": "create index if not exists formula_drug_delivered_id_ff5c08d9_like\n"
                  "    on formula_drug (delivered_id varchar_pattern_ops);",
        "drop_script": "drop index if exists formula_drug_delivered_id_ff5c08d9_like;",
        "order": 91,
        "collection": "Drug",
        "operation_type": "index",
        "comment": "NO ESTÁ CLARA SU UTILIDAD"
    },
    {
        "script": "create index if not exists formula_rx_delivered_final_id_331bd9fa_like\n"
                  "    on formula_rx (delivered_final_id varchar_pattern_ops);",
        "drop_script": "drop index if exists formula_rx_delivered_final_id_331bd9fa_like;",
        "order": 92,
        "collection": "Rx",
        "operation_type": "index",
        "comment": "NO ESTÁ CLARA SU UTILIDAD"
    },
    {
        "script": "create index if not exists formula_comprx_area_id_70b37bf9_like\n"
                  "    on formula_complementrx (area_id varchar_pattern_ops);",
        "drop_script": "drop index if exists formula_comprx_area_id_70b37bf9_like;",
        "order": 93,
        "collection": "Rx",
        "operation_type": "index",
        "comment": "NO ESTÁ CLARA SU UTILIDAD"
    },
    {
        "script": "create index if not exists formula_rx_medical_unit_id_27e254eb_like\n"
                  "    on formula_rx (medical_unit_id varchar_pattern_ops);",
        "drop_script": "drop index if exists formula_rx_medical_unit_id_27e254eb_like;",
        "order": 95,
        "collection": "Rx",
        "operation_type": "index",
        "comment": "NO ESTÁ CLARA SU UTILIDAD"
    },
    {
        "script": "create index if not exists formula_drug_medicament_id_630af6c3_like\n"
                  "    on formula_drug (medicament_id varchar_pattern_ops);",
        "drop_script": "drop index if exists formula_drug_medicament_id_630af6c3_like;",
        "order": 96,
        "collection": "Drug",
        "operation_type": "index",
        "comment": "NO ESTÁ CLARA SU UTILIDAD"
    },
    {
        "script": "create index if not exists formula_diagnosisrx_diagnosis_id_efb405f2_like\n"
                  "    on formula_diagnosisrx (diagnosis_id varchar_pattern_ops);",
        "drop_script": "drop index if exists formula_diagnosisrx_diagnosis_id_efb405f2_like;",
        "order": 97,
        "collection": "DiagnosisRx",
        "operation_type": "index",
        "comment": "NO ESTÁ CLARA SU UTILIDAD"
    },
    {
        "script": "create index if not exists formula_complementrx_area_id_b0ff963e_like\n"
                  "    on formula_complementrx (area_id varchar_pattern_ops);",
        "drop_script": "drop index if exists formula_complementrx_area_id_b0ff963e_like;",
        "order": 98,
        "collection": "ComplementRx",
        "operation_type": "index",
        "comment": "NO ESTÁ CLARA SU UTILIDAD"
    },
    {
        "script": "create index if not exists formula_complementrx_diagnosis_id_b7888698_like\n"
                  "    on formula_complementrx (diagnosis_id varchar_pattern_ops);",
        "drop_script": "drop index if exists formula_complementrx_diagnosis_id_b7888698_like;",
        "order": 99,
        "collection": "ComplementRx",
        "operation_type": "index",
        "comment": "NO ESTÁ CLARA SU UTILIDAD"
    },
]


def create_operations(reset=False):
    from rds.models import Operation, OperationGroup
    from data_param.models import Collection
    if reset:
        Operation.objects.all().delete()
        # OperationGroup.objects.all().delete()
    for operation in new_operations:
        has_percent = "\n" in operation["comment"]
        order = operation.get("order")
        low_priority = order >= 60
        comment = ""
        if has_percent:
            group_name, comment = operation["comment"].split("\n")
        else:
            group_name = operation["comment"]
        group_name = group_name.strip()
        group, created = OperationGroup.objects.get_or_create(name=group_name)
        if created and low_priority:
            group.low_priority = low_priority
            group.save()
        collection = Collection.objects.get(model_name=operation["collection"])
        Operation.objects.create(
            operation_type=operation["operation_type"],
            operation_group=group,
            order=order,
            low_priority=low_priority,
            is_active=True,
            collection=collection,
            script=operation["script"],
            script_drop=operation["drop_script"],
            comment=comment
        )



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

    # TODOS NUEVOS
    "alter table formula_complementrx  \n add constraint formula_complementrx_pkey \n primary key (uuid)",
    "alter table formula_complementrx  \n \nadd constraint formula_complementrx_age_check\n            check (age >= 0)",
    "create index if not exists formula_complementrx_area_id_b0ff963e\n    on formula_complementrx (area_id);",
    "alter table formula_complementrx  \n \nadd constraint formula_complementrx_area_id_b0ff963e_fk_med_cat_area_hex_hash\nforeign key (area_id) references med_cat_area\n            deferrable initially deferred",
    "create index if not exists formula_complementrx_diagnosis_id_b7888698\n    on formula_complementrx (diagnosis_id);",
    "alter table formula_complementrx  \n \nadd constraint formula_complementrx_diagnosis_id_b7888698_fk_med_cat_d\n   foreign key (diagnosis_id) references med_cat_diagnosis\n            deferrable initially deferred",
    "create index if not exists formula_complementrx_rx_id_02b25250\n    on formula_complementrx (rx_id);",
    "alter table formula_complementrx  \n \nadd constraint formula_complementrx_rx_id_02b25250_fk_formula_rx_uuid_folio\n   foreign key (rx_id) references formula_rx\n            deferrable initially deferred;",

    "alter table formula_complementdrug  \n add constraint formula_complementdrug_pkey \n primary key (uuid)",
    "create index if not exists formula_complementdrug_drug_id_9274b9d5\n    on formula_complementdrug (drug_id);"
    "alter table formula_complementdrug  \n \nadd constraint formula_complementdrug_drug_id_9274b9d5_fk_formula_drug_uuid\n   foreign key (drug_id) references formula_drug\n            deferrable initially deferred;",

    "create index if not exists formula_complementrx_diagnosis_id_b7888698_like\n    on formula_complementrx (diagnosis_id varchar_pattern_ops);",
    "create index if not exists formula_complementrx_area_id_b0ff963e_like\n    on formula_complementrx (area_id varchar_pattern_ops);",


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
