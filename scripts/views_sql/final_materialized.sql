-- TABLE mother_rx
SELECT
	rx.entity_id,
	rx.medical_unit_id,
	rx.year,
	rx.month,
	rx.delivered_final_id,
	COUNT(*)
FROM fm_55_201701_rx rx
GROUP BY
	rx.entity_id,
	rx.delivered_final_id,
	rx.year,
	rx.month,
	rx.medical_unit_id;


-- TABLE mother_drug_priority
SELECT
	med_unit.delegation_id,
	med_unit.clues_id,
	drug.entity_week_id,
	drug.delivered_id,
	cont.key,
	cont.id as container_id,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM fm_55_201907_rx rx
    JOIN med_cat_medicalunit med_unit ON rx.medical_unit_id = med_unit.hex_hash
    JOIN fm_55_201907_drug drug ON rx.uuid_folio = drug.rx_id
    JOIN med_cat_medicament med_cat ON drug.medicament_id = med_cat.hex_hash
    JOIN medicine_container cont ON cont.id = med_cat.container_id
    JOIN medicine_presentation pres ON pres.id = cont.presentation_id
    JOIN medicine_component comp ON comp.id = pres.component_id
WHERE comp.priority < 4
GROUP BY
    med_unit.delegation_id,
    med_unit.clues_id,
    drug.entity_week_id,
	drug.delivered_id,
	cont.key,
	cont.id;

-- Total rows: 1000 of 8145
-- Query complete 00:00:26.652
-- 2848.58 seconds => 47.5 minutes; 2480532 rows


CREATE INDEX mother_drug_priority_idx
    ON mother_drug_priority (delegation_id, clues_id, entity_week_id, delivered_id, container_id);
CREATE INDEX mother_drug_priority_delegation_idx
    ON mother_drug_priority (delegation_id);
-- create index if not exists formula_rx_doctor_id_6f41a184_like\n    on formula_rx (doctor_id varchar_pattern_ops);"
CREATE INDEX mother_drug_priority_clues_idx
    ON mother_drug_priority (clues_id);
CREATE INDEX mother_drug_priority_week_idx
    ON mother_drug_priority (entity_week_id);
CREATE INDEX mother_drug_priority_delivered_idx
    ON mother_drug_priority (delivered_id);
CREATE INDEX mother_drug_priority_container_idx
    ON mother_drug_priority (container_id);


SELECT
	med_unit.delegation_id,
	med_unit.clues_id,
	drug.entity_week_id,
	drug.delivered_id,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM fm_55_201907_rx rx
    JOIN med_cat_medicalunit med_unit ON rx.medical_unit_id = med_unit.hex_hash
    JOIN fm_55_201907_drug drug ON rx.uuid_folio = drug.rx_id
GROUP BY
    med_unit.delegation_id,
    med_unit.clues_id,
    drug.entity_week_id,
	drug.delivered_id;

-- Total rows: 863 of 863
-- Query complete 00:00:40.400



CREATE INDEX mother_drug_totals_idx
    ON mother_drug_totals (delegation_id, clues_id, entity_week_id, delivered_id);
CREATE INDEX mother_drug_totals_delegation_idx
    ON mother_drug_totals (delegation_id);
CREATE INDEX mother_drug_totals_clues_idx
    ON mother_drug_totals (clues_id);
CREATE INDEX mother_drug_totals_week_idx
    ON mother_drug_totals (entity_week_id);
CREATE INDEX mother_drug_totals_delivered_idx
    ON mother_drug_totals (delivered_id);


-- TABLE mother_drug
SELECT
	med_unit.delegation_id,
	med_unit.clues_id,
	drug.entity_week_id,
	drug.delivered_id,
	cont.key,
	cont.id as container_id,
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered,
	COUNT(*) as total
FROM fm_55_201702_rx rx
    JOIN med_cat_medicalunit med_unit ON rx.medical_unit_id = med_unit.hex_hash
    JOIN fm_55_201702_drug drug ON rx.uuid_folio = drug.rx_id
    JOIN med_cat_medicament med_cat ON drug.medicament_id = med_cat.hex_hash
    JOIN medicine_container cont ON cont.id = med_cat.container_id
    JOIN medicine_presentation pres ON pres.id = cont.presentation_id
    JOIN medicine_component comp ON comp.id = pres.component_id
GROUP BY
    med_unit.delegation_id,
    med_unit.clues_id,
    drug.entity_week_id,
	drug.delivered_id,
	cont.key,
	cont.id;


CREATE INDEX mother_drug_idx
    ON mother_drug (delegation_id, clues_id, entity_week_id, delivered_id, container_id);
CREATE INDEX mother_drug_idx2
    ON mother_drug (entity_week_id, container_id);
CREATE INDEX mother_drug_delegation_idx
    ON mother_drug (delegation_id);
CREATE INDEX mother_drug_clues_idx
    ON mother_drug (clues_id);
CREATE INDEX mother_drug_week_idx
    ON mother_drug (entity_week_id);
CREATE INDEX mother_drug_delivered_idx
    ON mother_drug (delivered_id);


-- TABLE mother_drug_extended
SELECT
    md.delegation_id,
    ew.iso_year,
    ew.iso_week,
    ew.entity_id,
    md.container_id,
    cont.presentation_id,
    pres.component_id,
    SUM (md.prescribed) as prescribed,
    SUM (md.delivered) as delivered,
    SUM (md.total) as total
FROM mother_drug md
JOIN inai_entityweek ew ON md.entity_week_id = ew.id
JOIN medicine_container cont ON md.container_id = cont.id
JOIN medicine_presentation pres ON pres.id = cont.presentation_id
GROUP BY
    md.delegation_id,
    ew.iso_year,
    ew.iso_week,
    ew.entity_id,
    md.container_id,
    cont.presentation_id,
    pres.component_id;


CREATE INDEX mother_drug_extended_idx
    ON mother_drug_extended (delegation_id, iso_year, iso_week, entity_id, component_id);
CREATE INDEX mother_drug_extended_delegation_idx
    ON mother_drug_extended (delegation_id);
CREATE INDEX mother_drug_extended_year_idx
    ON mother_drug_extended (iso_year);
CREATE INDEX mother_drug_extended_week_idx
    ON mother_drug_extended (iso_week);
CREATE INDEX mother_drug_extended_entity_idx
    ON mother_drug_extended (entity_id);
CREATE INDEX mother_drug_extended_component_idx
    ON mother_drug_extended (component_id);
CREATE INDEX mother_drug_extended_container_idx
    ON mother_drug_extended (container_id);
CREATE INDEX mother_drug_extended_presentation_idx
    ON mother_drug_extended (presentation_id);



