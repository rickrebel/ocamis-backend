-- prescription

alter table public.formula_prescription
    add constraint formula_prescription_iso_year_check
        check (iso_year >= 0),

    add constraint formula_prescription_iso_week_check
        check (iso_week >= 0),

    add constraint formula_prescription_iso_day_check
        check (iso_day >= 0),

    add constraint formula_prescription_month_check
        check (month >= 0),

    add constraint formula_prescription_data_file_id_ef911d11_fk_inai_datafile_id
        foreign key (data_file_id) references public.inai_datafile
            deferrable initially deferred,


    add constraint formula_prescription_area_id_70b37bf9_fk_catalog_area_id
        foreign key (area_id) references public.catalog_area
            deferrable initially deferred,

    add constraint formula_prescription_clues_id_7b015cda_fk_desabasto_clues_id
        foreign key (clues_id) references public.desabasto_clues
            deferrable initially deferred,

    add constraint formula_prescription_delegation_id_0b8cad2e_fk_catalog_d
        foreign key (delegation_id) references public.catalog_delegation
            deferrable initially deferred,

    add constraint formula_prescription_delivered_final_id_331bd9fa_fk_formula_d
        foreign key (delivered_final_id) references public.formula_delivered
            deferrable initially deferred,

    add constraint formula_prescription_doctor_id_6f41a184_fk_formula_doctor_uuid
        foreign key (doctor_id) references public.formula_doctor
            deferrable initially deferred;

create index formula_prescription_data_file_id_ef911d11
    on public.formula_prescription (data_file_id);

create index formula_prescription_area_id_70b37bf9
    on public.formula_prescription (area_id);

create index formula_prescription_clues_id_7b015cda
    on public.formula_prescription (clues_id);

create index formula_prescription_delegation_id_0b8cad2e
    on public.formula_prescription (delegation_id);

create index formula_prescription_delivered_id_8c182a3e
    on public.formula_prescription (delivered_final_id);

create index formula_prescription_delivered_id_8c182a3e_like
    on public.formula_prescription (delivered_final_id varchar_pattern_ops);

create index formula_prescription_doctor_id_6f41a184
    on public.formula_prescription (doctor_id);

-- drug

alter table public.formula_drug
    add constraint formula_drug_pkey
        primary key (uuid),

    add constraint formula_drug_prescribed_amount_check
        check (prescribed_amount >= 0),

    add constraint formula_drug_delivered_amount_check
        check (delivered_amount >= 0),

    add constraint formula_drug_row_seq_check
        check (row_seq >= 0),

    add constraint formula_drug_container_id_902ff1c3_fk_desabasto_container_id
        foreign key (container_id) references public.desabasto_container
            deferrable initially deferred,

    --add constraint formula_drug_data_file_id_e47b8ac0_fk_inai_datafile_id
    --    foreign key (data_file_id) references public.inai_datafile
    --        deferrable initially deferred,

    add constraint formula_drug_delivered_id_ff5c08d9_fk_formula_d
        foreign key (delivered_id) references public.formula_delivered
            deferrable initially deferred,

    add constraint formula_drug_prescription_id_cdf044b3_fk_formula_p
        foreign key (prescription_id) references public.formula_prescription
            deferrable initially deferred;


create index formula_drug_container_id_902ff1c3
    on public.formula_drug (container_id);

--create index formula_drug_data_file_id_e47b8ac0
--    on public.formula_drug (data_file_id);

create index formula_drug_delivered_id_ff5c08d9
    on public.formula_drug (delivered_id);

create index formula_drug_delivered_id_ff5c08d9_like
    on public.formula_drug (delivered_id varchar_pattern_ops);

create index formula_drug_prescription_id_cdf044b3
    on public.formula_drug (prescription_id);

-- missing rows

alter table public.formula_missingrow
    add constraint formula_missingrow_drug_id_746af424_fk_formula_drug_uuid
        foreign key (drug_id) references public.formula_drug
            deferrable initially deferred,

    add constraint formula_missingrow_data_file_id_0598960b_fk_inai_datafile_id
        foreign key (data_file_id) references public.inai_datafile
            deferrable initially deferred,

    add constraint formula_missingrow_prescription_id_f6fbc500_fk_formula_p
        foreign key (prescription_id) references public.formula_prescription
            deferrable initially deferred;


alter table public.formula_missingrow
    owner to postgres;

create index formula_missingrow_drug_id_746af424
    on public.formula_missingrow (drug_id);

create index formula_missingrow_file_id_c4e90440
    on public.formula_missingrow (data_file_id);

create index formula_missingrow_prescription_id_f6fbc500
    on public.formula_missingrow (prescription_id);

-- missing fields

alter table public.formula_missingfield
    add constraint formula_missingfield_missing_row_id_8903ee88_fk_formula_m
        foreign key (missing_row_id) references public.formula_missingrow
            deferrable initially deferred,

    add constraint formula_missingfield_name_column_id_d2bc6a65_fk_inai_name
        foreign key (name_column_id) references public.data_param_namecolumn
            deferrable initially deferred;

alter table public.formula_missingfield
    owner to user_desabasto;

create index formula_missingfield_missing_row_id_8903ee88
    on public.formula_missingfield (missing_row_id);

create index formula_missingfield_name_column_id_d2bc6a65
    on public.formula_missingfield (name_column_id);
