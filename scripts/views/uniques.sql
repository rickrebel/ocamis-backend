 SELECT
    drug.sheet_file_id AS sheet_id,
    pres.entity_id,
    pres.folio_ocamis,
	pres.month,
	pres.iso_week,
	pres.iso_year,
    pres.uuid_folio,
    pres.delivered_final_id AS delivered
   FROM formula_prescription pres
     JOIN formula_drug drug ON pres.uuid_folio = drug.prescription_id;


 SELECT
    sheetfile.id AS sheetfile_id,
    datafile.entity_id
    FROM
        inai_sheetfile sheetfile
        JOIN inai_datafile datafile ON sheetfile.data_file_id = datafile.id
    WHERE
        sheetfile.behavior_id::text = 'need_merge'::text OR sheetfile.behavior_id::text = 'merged'::text;


SELECT
    delivered_final_id,
    COUNT(delivered_final_id) AS total
FROM formula_prescription
GROUP BY delivered_final_id;

