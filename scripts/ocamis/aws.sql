CREATE TABLE events (event_id integer primary key, event_name varchar(120) NOT NULL, event_value
varchar(256) NOT NULL);

SELECT conname, conrelid::regclass, contype
FROM pg_constraint
WHERE conrelid = 'formula_drug'::regclass;

SELECT conname, conrelid::regclass, contype
FROM pg_constraint
WHERE conrelid = 'formula_prescription'::regclass;

SELECT conname, conrelid::regclass, contype
FROM pg_constraint
WHERE conrelid = 'formula_missing_row'::regclass;


ALTER TABLE formula_missingrow DROP CONSTRAINT formula_missingrow_drug_id_746af424_fk_formula_drug_uuid
ALTER TABLE formula_missingrow DROP CONSTRAINT formula_missingrow_prescription_id_f6fbc500_fk_formula_p


ALTER TABLE formula_drug DROP CONSTRAINT formula_drug_pkey

ALTER TABLE formula_drug DROP CONSTRAINT formula_drug_prescribed_amount_check
ALTER TABLE formula_drug DROP CONSTRAINT formula_drug_delivered_amount_check
ALTER TABLE formula_drug DROP CONSTRAINT formula_drug_row_seq_check
ALTER TABLE formula_drug DROP CONSTRAINT formula_drug_prescription_id_cdf044b3_fk_formula_p
ALTER TABLE formula_drug DROP CONSTRAINT formula_drug_container_id_902ff1c3_fk_desabasto_container_id
ALTER TABLE formula_drug DROP CONSTRAINT formula_drug_data_file_id_e47b8ac0_fk_inai_datafile_id
ALTER TABLE formula_drug DROP CONSTRAINT formula_drug_delivered_id_ff5c08d9_fk_formula_d


ALTER TABLE formula_prescription DROP CONSTRAINT formula_prescription_pkey;

ALTER TABLE formula_prescription DROP CONSTRAINT formula_prescription_iso_year_check;
ALTER TABLE formula_prescription DROP CONSTRAINT formula_prescription_iso_week_check;
ALTER TABLE formula_prescription DROP CONSTRAINT formula_prescription_iso_day_check;
ALTER TABLE formula_prescription DROP CONSTRAINT formula_prescription_area_id_70b37bf9_fk_catalog_area_id;
ALTER TABLE formula_prescription DROP CONSTRAINT formula_prescription_clues_id_7b015cda_fk_desabasto_clues_id;
ALTER TABLE formula_prescription DROP CONSTRAINT formula_prescription_doctor_id_6f41a184_fk_formula_doctor_uuid;
ALTER TABLE formula_prescription DROP CONSTRAINT formula_prescription_month_check;
ALTER TABLE formula_prescription DROP CONSTRAINT formula_prescription_delegation_id_0b8cad2e_fk_catalog_d;
ALTER TABLE formula_prescription DROP CONSTRAINT formula_prescription_delivered_final_id_331bd9fa_fk_formula_d;


SELECT indexname FROM pg_indexes WHERE tablename = 'formula_drug';

DROP INDEX formula_drug_container_id_902ff1c3;
DROP INDEX formula_drug_data_file_id_e47b8ac0;
DROP INDEX formula_drug_delivered_id_ff5c08d9;
DROP INDEX formula_drug_delivered_id_ff5c08d9_like;
DROP INDEX formula_drug_prescription_id_cdf044b3;

SELECT indexname FROM pg_indexes WHERE tablename = 'formula_prescription';


DROP INDEX formula_prescription_area_id_70b37bf9;
DROP INDEX formula_prescription_clues_id_7b015cda;
DROP INDEX formula_prescription_delegation_id_0b8cad2e;
DROP INDEX formula_prescription_delivered_id_8c182a3e;
DROP INDEX formula_prescription_delivered_id_8c182a3e_like;
DROP INDEX formula_prescription_doctor_id_6f41a184;


SELECT aws_s3.table_import_from_s3(
'POSTGRES_TABLE_NAME', 'event_id,event_name,event_value', '(format csv, header true)',
'BUCKET_NAME',
'FOLDER_NAME(optional)/FILE_NAME',
'REGION',
'AWS_ACCESS_KEY', 'AWS_SECRET_KEY', 'OPTIONAL_SESSION_TOKEN'
)


CREATE TABLE events (event_id integer primary key, event_name varchar(120) NOT NULL, event_value varchar(256) NOT NULL);


SELECT aws_s3.table_import_from_s3(
'events', 'event_id,event_name,event_value', '(format csv, header true)',
'cdn-desabasto',
'data_files/example.csv',
'us-west-2',
'AKIAICSGL3ROH3GVALGQ', 'fFq7NwQyj/FmdtK/weXRwgrlEArkOatITD/mJYzL'
)


SELECT month, iso_year, delivered_final_id, COUNT(*) as file_count
FROM formula_prescription
GROUP BY month, iso_year, delivered_final_id;
