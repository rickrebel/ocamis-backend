SELECT
	med_unit.delegation_id,
	med_unit.clues_id,
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


