SELECT
	med_unit.delegation_id,
-- 	med_unit.clues_id,
-- 	drug.entity_week_id,
	week.iso_year,
	week.iso_week,
	week.year,
	week.month,
	drug.delivered_id,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM fm_55_201907_rx rx
    JOIN med_cat_medicalunit med_unit ON rx.medical_unit_id = med_unit.hex_hash
    JOIN fm_55_201907_drug drug ON rx.uuid_folio = drug.rx_id
    JOIN inai_entityweek week ON drug.entity_week_id = week.id
GROUP BY
    med_unit.delegation_id,
    med_unit.clues_id,
    week.iso_year,
    week.iso_week,
    week.year,
    week.month,
	drug.delivered_id;

-- Total rows: 863 of 863
-- Query complete 00:01:02.257



SELECT
	week.iso_year,
	week.iso_week,
	week.entity_id,
	week.year,
	week.month,
	drug.delivered_id,
	drug.medicament_id,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM fm_55_201907_drug drug
JOIN inai_entityweek week ON drug.week_record_id = week.id
GROUP BY
    week.iso_year,
    week.iso_week,
    week.entity_id,
    week.year,
    week.month,
	drug.delivered_id,
	drug.medicament_id;



SELECT
	drug.entity_week_id,
	drug.delivered_id,
	drug.medicament_id,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM fm_55_201907_drug drug
GROUP BY
	drug.entity_week_id,
	drug.delivered_id,
	drug.medicament_id;

-- Total rows: 1000 of 163743
-- Query complete 00:00:19.862


SELECT
	gen_random_uuid() AS uuid,
	'CLUSTER_NAME'::text AS cluster_id,
	med_unit.delegation_id,
	drug.week_record_id,
	drug.delivered_id,
	SUM (drug.prescribed_amount) as prescribed_total,
	SUM (drug.delivered_amount) as delivered_total,
	COUNT(*) as total
FROM formula_rx rx
	JOIN public.med_cat_medicalunit med_unit ON rx.medical_unit_id = med_unit.hex_hash
	JOIN formula_drug drug ON rx.uuid_folio = drug.rx_id
	JOIN public.inai_entityweek week ON drug.week_record_id = week.id
GROUP BY
	med_unit.delegation_id,
	drug.week_record_id,
	drug.delivered_id;

SELECT
	week.iso_year,
	week.iso_week,
	week.provider_id AS entity_id,
	week.year,
	week.month,
	drug.delivered_id,
	drug.medicament_id,
	sum(drug.prescribed_amount) AS prescribed,
	sum(drug.delivered_amount) AS delivered,
	count(*) AS total
FROM formula_drug drug
	JOIN inai_entityweek week ON drug.week_record_id = week.id
GROUP BY
	week.iso_year,
	week.iso_week,
	week.provider_id,
	week.year,
	week.month,
	drug.delivered_id,
	drug.medicament_id;


SELECT
	gen_random_uuid() AS uuid,
	'CLUSTER_NAME'::text AS cluster_id,
	drug.week_record_id,
	drug.delivered_id,
	drug.medicament_id,
	sum(drug.prescribed_amount) AS prescribed_total,
	sum(drug.delivered_amount) AS delivered_total,
	count(*) AS total
FROM formula_drug drug
GROUP BY
	drug.week_record_id,
	drug.delivered_id,
	drug.medicament_id;

--command " "\\copy public.mat_drug_totals2 (uuid, cluster_id, delegation_id, week_record_id, delivered_id, prescribed_total, delivered_total, total) FROM 'C:/Users/Ricardo/DOWNLO~1/DA7428~1.CSV' DELIMITER ',' CSV HEADER ENCODING 'UTF8' QUOTE '\"' NULL 'NULL' ESCAPE '''';""
-- SELECT
-- 	gen_random_uuid() AS uuid,
-- 	'first'::text AS cluster,
-- 	delegation_id,
-- 	week_record_id,
-- 	delivered_id,
-- 	SUM (prescribed_total) as prescribed_total,
-- 	SUM (delivered_total) as delivered_total,
-- 	SUM (total) as total
-- from mat_drug_totals
-- GROUP BY
-- 	delegation_id,
-- 	week_record_id,
-- 	delivered_id;

-- SELECT aws_s3.table_import_from_s3(
-- 	'public.provisional_mat_drug',
-- 	'uuid,cluster_id,week_record_id,delivered_id,medicament_id,prescribed_total,delivered_total,total',
-- 	'(format csv, header true, delimiter "|", encoding "UTF8")',
-- 	'cdn-desabasto',
-- 	'data_files/mat_views/mat_drug_entity2.csv',
--  ...
-- );

-- SELECT aws_commons.create_s3_uri(
--    'cdn-desabasto',
--    'data_files/mat_views/mat_drug_entity2.csv',
--    'us-west-2'
-- ) AS s3_uri


SELECT
	gen_random_uuid() AS uuid,
	'first'::text AS cluster_id,
	week.id AS week_record_id,
	mde.delivered_id,
	mde.medicament_id,
	SUM (mde.prescribed_total) as prescribed_total,
	SUM (mde.delivered_total) as delivered_total,
	SUM (mde.total) as total
from mat_drug_entity mde
    JOIN (SELECT *
        FROM public.inai_entityweek week
        WHERE week.iso_delegation_id IS NULL) week
        ON week.year = mde.year AND week.month = mde.month
         AND week.iso_year = mde.iso_year AND week.iso_week = mde.iso_week
         AND week.provider_id = mde.entity_id
GROUP BY
	week.id,
    mde.delivered_id,
    mde.medicament_id;


