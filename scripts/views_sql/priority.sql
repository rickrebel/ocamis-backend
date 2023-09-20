
SELECT
	rx.entity_id,
	rx.medical_unit_id,
	drug.entity_week_id,
	drug.delivered_id,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM fm_55_201907_rx rx
JOIN fm_55_201907_drug drug ON rx.uuid_folio = drug.rx_id
JOIN med_cat_medicament med ON drug.medicament_id = med.hex_hash
WHERE med.container_id = 43
GROUP BY
    rx.entity_id,
    rx.medical_unit_id,
	drug.entity_week_id,
	drug.delivered_id,
	drug.medicament_id;


-- Total rows: 1000 of 15136
-- Query complete 00:00:25.482
-- Finished  48283.95 seconds => 13.4 hours
-- 1042296 rows



SELECT
	rx.entity_id,
	rx.medical_unit_id,
	drug.entity_week_id,
	drug.delivered_id,
	cont.id as container_id,
	cont.key as key,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM fm_55_201907_rx rx
    JOIN fm_55_201907_drug drug ON rx.uuid_folio = drug.rx_id
    JOIN med_cat_medicament med_cat ON drug.medicament_id = med_cat.hex_hash
    -- JOIN view_medicine med2 ON med_cat.container_id = med2.container_id
    JOIN medicine_container cont ON cont.id = med_cat.container_id
    JOIN medicine_presentation pres ON pres.id = cont.presentation_id
    JOIN medicine_component comp ON comp.id = pres.component_id
WHERE comp.priority < 4
-- WHERE med2.priority < 4
GROUP BY
    rx.entity_id,
    rx.medical_unit_id,
	drug.entity_week_id,
	drug.delivered_id,
	drug.medicament_id,
	cont.id,
	cont.key;

-- Total rows: 1000 of 109359
-- Query complete 00:00:38.749


SELECT
	rx.entity_id,
	rx.medical_unit_id,
	drug.entity_week_id,
	drug.delivered_id,
	med2.container_id,
	med2.key,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM fm_55_201907_rx rx
    JOIN fm_55_201907_drug drug ON rx.uuid_folio = drug.rx_id
    JOIN med_cat_medicament med_cat ON drug.medicament_id = med_cat.hex_hash
    JOIN view_medicine med2 ON med_cat.container_id = med2.container_id
WHERE med2.priority < 4
GROUP BY
    rx.entity_id,
    rx.medical_unit_id,
	drug.entity_week_id,
	drug.delivered_id,
	drug.medicament_id,
	med2.container_id,
	med2.key;

-- Total rows: 1000 of 109359
-- Query complete 00:00:38.880


SELECT
	rx.entity_id,
	rx.medical_unit_id,
	drug.entity_week_id,
	drug.delivered_id,
	comp.id as component_id,
	pres.id as presentation_id,
	cont.id as container_id,
	comp.name as component_name,
	pres.description as presentation_name,
	cont.name as container_name,
	cont.key as key,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM fm_55_201907_rx rx
    JOIN fm_55_201907_drug drug ON rx.uuid_folio = drug.rx_id
    JOIN med_cat_medicament med_cat ON drug.medicament_id = med_cat.hex_hash
    -- JOIN view_medicine med2 ON med_cat.container_id = med2.container_id
    JOIN medicine_container cont ON cont.id = med_cat.container_id
    JOIN medicine_presentation pres ON pres.id = cont.presentation_id
    JOIN medicine_component comp ON comp.id = pres.component_id
WHERE comp.priority < 4
-- WHERE med2.priority < 4
GROUP BY
    rx.entity_id,
    rx.medical_unit_id,
	drug.entity_week_id,
	drug.delivered_id,
	drug.medicament_id,
	comp.id,
	pres.id,
	cont.id,
	comp.name,
	pres.description,
	cont.name,
	cont.key;

-- 1000 of 109359
-- Query complete 00:00:44.007


SELECT
	rx.entity_id,
	med_unit.delegation_id,
	med_unit.clues_id,
	drug.entity_week_id,
	drug.delivered_id,
	comp.id as component_id,
	pres.id as presentation_id,
	cont.id as container_id,
	comp.name as component_name,
	pres.description as presentation_name,
	cont.name as container_name,
	cont.key as key,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM fm_55_201907_rx rx
    JOIN med_cat_medicalunit med_unit ON rx.medical_unit_id = med_unit.hex_hash
    JOIN fm_55_201907_drug drug ON rx.uuid_folio = drug.rx_id
    JOIN med_cat_medicament med_cat ON drug.medicament_id = med_cat.hex_hash
    -- JOIN view_medicine med2 ON med_cat.container_id = med2.container_id
    JOIN medicine_container cont ON cont.id = med_cat.container_id
    JOIN medicine_presentation pres ON pres.id = cont.presentation_id
    JOIN medicine_component comp ON comp.id = pres.component_id
WHERE comp.priority < 4
-- WHERE med2.priority < 4
GROUP BY
    rx.entity_id,
    med_unit.delegation_id,
    med_unit.clues_id,
	drug.entity_week_id,
	drug.delivered_id,
	drug.medicament_id,
	comp.id,
	pres.id,
	cont.id,
	comp.name,
	pres.description,
	cont.name,
	cont.key;

-- Total rows: 1000 of 8145
-- Query complete 00:00:40.417
