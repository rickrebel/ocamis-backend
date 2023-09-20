SELECT
    inst.code AS code,
    ent.name AS entity_name,
    rx.iso_year,
    rx.month,
    deliv.name AS delivered_short_name,
    COUNT(drug.uuid) AS drugs_count,
    SUM(drug.prescribed_amount) AS total_prescribed_amount,
    SUM(drug.delivered_amount) AS total_delivered_amount
FROM
    geo_entity ent
    JOIN geo_institution inst ON ent.institution_id = inst.id
    JOIN formula_rx rx ON ent.id = rx.entity_id
    JOIN formula_drug drug ON rx.uuid_folio = drug.rx_id
    JOIN med_cat_delivered deliv ON drug.delivered_id = deliv.hex_hash
GROUP BY
    ent.name,
    inst.code,
    rx.iso_year,
    rx.month,
    deliv.name
ORDER BY
    ent.name,
    inst.code,
    rx.iso_year,
    rx.month,
    deliv.name;


SELECT
    inst.code AS code,
    ent.name AS entity_name,
    ew.month,
    ew.year,
    SUM(ew.rx_count) as rx_count,
    SUM(ew.zero) as zero,
    SUM(ew.unknown) as unknown,
    SUM(ew.unavailable) as unavailable,
    SUM(ew.partial) as partial,
    SUM(ew.over_delivered) as over_delivered,
    SUM(ew.error) as error,
    SUM(ew.denied) as denied,
    SUM(ew.complete) as complete,
    SUM(ew.cancelled) as cancelled
FROM
    geo_entity ent
    JOIN inai_entityweek as ew ON ent.id = ew.entity_id
    JOIN geo_institution inst ON ent.institution_id = inst.id
WHERE
    ent.id = 55
GROUP BY
    ent.name,
    inst.code,
    ew.month,
    ew.year
ORDER BY
    ent.name,
    inst.code,
	ew.year,
    ew.month;



SELECT
    inst.code AS code,
    ent.name AS entity_name,
    deleg.name AS delegation_name,
    ew.month,
    ew.year,
    SUM(ew.rx_count) as rx_count,
    SUM(ew.zero) as zero,
    SUM(ew.unknown) as unknown,
    SUM(ew.unavailable) as unavailable,
    SUM(ew.partial) as partial,
    SUM(ew.over_delivered) as over_delivered,
    SUM(ew.error) as error,
    SUM(ew.denied) as denied,
    SUM(ew.complete) as complete,
    SUM(ew.cancelled) as cancelled
FROM
    geo_entity ent
    JOIN inai_entityweek as ew ON ent.id = ew.entity_id
    JOIN geo_delegation as deleg ON deleg.id = ew.iso_delegation
    JOIN geo_institution inst ON ent.institution_id = inst.id
WHERE
    ent.id = 55
GROUP BY
    ent.name,
    delegation_name,
    inst.code,
    ew.month,
    ew.year
ORDER BY
	ew.year,
    ew.month,
    inst.code,
    ent.name,
    delegation_name;




SELECT
    inst.code AS code,
    ent.name AS entity_name,
    rx.iso_year,
    rx.month,
    df2.name AS deliv_drug,
    df.name AS deliv_pres,
    COUNT(DISTINCT rx.uuid_folio) AS rx_count,
    COUNT(*) AS total_drug
    -- SUM(drug.prescribed_amount) AS total_prescribed_amount,
    -- SUM(drug.delivered_amount) AS total_delivered_amount
FROM
    geo_entity ent
    JOIN geo_institution inst ON ent.institution_id = inst.id
    JOIN formula_rx rx ON ent.id = rx.entity_id
    JOIN formula_drug drug ON rx.uuid_folio = drug.rx_id
    JOIN med_cat_delivered df ON rx.delivered_final_id = df.hex_hash
    JOIN med_cat_delivered df2 ON drug.delivered_id = df2.hex_hash
GROUP BY
    ent.name,
    inst.code,
    rx.iso_year,
    rx.month,
    df.name,
    df2.name
ORDER BY
    ent.name,
    inst.code,
    rx.iso_year,
    rx.month,
    df.name,
    df2.name;




SELECT
    inst.code AS code,
    ent.name AS entity_name,
    rx.iso_year,
    rx.month,
    df.name AS delivered_short_name,
    COUNT(rx.uuid_folio) AS rx_count
FROM
    geo_entity ent
    JOIN geo_institution inst ON ent.institution_id = inst.id
    JOIN formula_rx rx ON ent.id = rx.entity_id
    JOIN med_cat_delivered df ON rx.delivered_final_id = df.hex_hash
    JOIN formula_drug drug ON rx.uuid_folio = drug.rx_id
    JOIN inai_sheetfile sheet ON drug.sheet_file_id = sheet.id
WHERE
    sheet.behavior_id != 'invalid'
GROUP BY
    ent.name,
    inst.code,
    rx.iso_year,
    rx.month,
    df.name
ORDER BY
    ent.name,
    inst.code,
    rx.iso_year,
    rx.month,
    df.name;





SELECT
    rx.iso_year,
    rx.month,
    rx.delivered_final_id,
    COUNT(rx.uuid_folio) AS rx_count
FROM
    formula_rx rx
GROUP BY
    rx.iso_year,
    rx.month,
    rx.delivered_final_id
ORDER BY
    rx.iso_year,
    rx.month,
    rx.delivered_final_id;





SELECT
	rx.medical_unit_id,
	drug.entity_week_id,
	drug.delivered_id,
	drug.medicament_id,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM fm_55_201907_rx rx
JOIN fm_55_201907_drug drug ON rx.uuid_folio = drug.rx_id
GROUP BY
    rx.medical_unit_id,
	drug.entity_week_id,
	drug.delivered_id,
	drug.medicament_id;

-- Total rows: 1000 of 1815441
-- Query complete 00:01:58.298


SELECT
    unit.entity_id,
	rx.medical_unit_id,
	drug.entity_week_id,
	drug.delivered_id,
	drug.medicament_id,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM fm_55_201907_rx rx
JOIN fm_55_201907_drug drug ON rx.uuid_folio = drug.rx_id
JOIN med_cat_medicalunit unit ON rx.medical_unit_id = unit.hex_hash
GROUP BY
    unit.entity_id,
    rx.medical_unit_id,
	drug.entity_week_id,
	drug.delivered_id,
	drug.medicament_id;

-- Total rows: 1000 of 1815441
-- Query complete 00:02:09.034


SELECT
    unit.entity_id,
	drug.entity_week_id,
	drug.delivered_id,
	drug.medicament_id,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM fm_55_201907_rx rx
JOIN fm_55_201907_drug drug ON rx.uuid_folio = drug.rx_id
JOIN med_cat_medicalunit unit ON rx.medical_unit_id = unit.hex_hash
GROUP BY
    unit.entity_id,
	drug.entity_week_id,
	drug.delivered_id,
	drug.medicament_id;

-- Total rows: 1000 of 163743
-- Query complete 00:00:47.291


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
JOIN inai_entityweek week ON drug.entity_week_id = week.id
GROUP BY
    week.iso_year,
    week.iso_week,
    week.entity_id,
    week.year,
    week.month,
	drug.delivered_id,
	drug.medicament_id;

-- Total rows: 1000 of 8782
-- Query complete 00:00:12.874


SELECT
	week.iso_year,
	week.iso_week,
	week.entity_id,
	week.year,
	week.month,
	med.container_id,
	drug.delivered_id,
	drug.medicament_id,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM fm_55_201907_drug drug
JOIN inai_entityweek week ON drug.entity_week_id = week.id
JOIN med_cat_medicament med ON drug.medicament_id = med.hex_hash
WHERE med.container_id IS NOT NULL
GROUP BY
    week.iso_year,
    week.iso_week,
    week.entity_id,
    week.year,
    week.month,
    med.container_id,
	drug.delivered_id,
	drug.medicament_id;

-- Total rows: 1000 of 8638
-- Query complete 00:00:42.722


SELECT
    unit.entity_id,
    unit.delegation_name,
	drug.entity_week_id,
	drug.delivered_id,
	drug.medicament_id,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM fm_55_201907_rx rx
JOIN fm_55_201907_drug drug ON rx.uuid_folio = drug.rx_id
JOIN med_cat_medicalunit unit ON rx.medical_unit_id = unit.hex_hash
GROUP BY
    unit.entity_id,
    unit.delegation_name,
	drug.entity_week_id,
	drug.delivered_id,
	drug.medicament_id;

-- Total rows: 1000 of 163743
-- Query complete 00:01:46.900


SELECT
    unit.entity_id,
    unit.delegation_name,
	drug.delivered_id,
	drug.medicament_id,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM fm_55_201907_rx rx
JOIN fm_55_201907_drug drug ON rx.uuid_folio = drug.rx_id
JOIN med_cat_medicalunit unit ON rx.medical_unit_id = unit.hex_hash
GROUP BY
    unit.entity_id,
    unit.delegation_name,
	drug.delivered_id,
	drug.medicament_id;

-- Total rows: 1000 of 44840
-- Query complete 00:02:02.051

SELECT
	rx.entity_id,
	rx.medical_unit_id,
	rx.year,
	rx.month,
	rx.iso_year,
	rx.iso_week,
	drug.delivered_id,
	drug.medicament_id,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM fm_55_201907_rx rx
JOIN fm_55_201907_drug drug ON rx.uuid_folio = drug.rx_id
GROUP BY
	rx.entity_id,
	rx.medical_unit_id,
	rx.year,
	rx.month,
	rx.iso_year,
	rx.iso_week,
	drug.delivered_id,
	drug.medicament_id;

-- Total rows: 1000 of 1815441
-- Query complete 00:02:43.846


SELECT
	rx.entity_id,
	rx.year,
	rx.month,
	rx.iso_year,
	rx.iso_week,
	drug.delivered_id,
	drug.medicament_id,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM fm_55_201907_rx rx
JOIN fm_55_201907_drug drug ON rx.uuid_folio = drug.rx_id
GROUP BY
	rx.entity_id,
	rx.year,
	rx.month,
	rx.iso_year,
	rx.iso_week,
	drug.delivered_id,
	drug.medicament_id;

-- Total rows: 1000 of 8782
-- Query complete 00:00:41.318


SELECT
    delivered_final_id,
    COUNT(delivered_final_id) AS total
FROM formula_rx
GROUP BY delivered_final_id;




SELECT
	unit.entity_id,
	rx.medical_unit_id,
	drug.entity_week_id,
	drug.delivered_id,
	drug.medicament_id,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM fm_55_201907_rx rx
JOIN fm_55_201907_drug drug ON rx.uuid_folio = drug.rx_id
JOIN med_cat_medicalunit unit ON rx.medical_unit_id = unit.hex_hash
WHERE rx.medical_unit_id IN (
	'9296a552300ea590b2484ba15c1514f3',
	'3d3910e9a82d8a2fe5a6897a2eb2e8b3',
	'df7c9dec7a13b8c7036912f2dece3c20')
GROUP BY
	unit.entity_id,
    rx.medical_unit_id,
	drug.entity_week_id,
	drug.delivered_id,
	drug.medicament_id;

-- Total rows: 1000 of 4020
-- Query complete 00:00:00.771

SELECT
	unit.entity_id,
	rx.medical_unit_id,
	drug.entity_week_id,
	drug.delivered_id,
	drug.medicament_id,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM formula_rx rx
JOIN formula_drug drug ON rx.uuid_folio = drug.rx_id
JOIN med_cat_medicalunit unit ON rx.medical_unit_id = unit.hex_hash
WHERE rx.medical_unit_id IN (
	'9296a552300ea590b2484ba15c1514f3',
	'3d3910e9a82d8a2fe5a6897a2eb2e8b3',
	'df7c9dec7a13b8c7036912f2dece3c20')
GROUP BY
	unit.entity_id,
    rx.medical_unit_id,
	drug.entity_week_id,
	drug.delivered_id,
	drug.medicament_id;

-- Total rows: 1000 of 197675
-- Query complete 00:24:49.706



