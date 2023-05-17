-- drugs_and_prescriptions
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


-- drugs_and_prescriptions_valid
 SELECT vsf.sheet_id,
    vsf.entity_id,
    pres.folio_ocamis,
    pres.month,
    pres.iso_week,
    pres.iso_year,
    pres.uuid_folio,
    pres.delivered_final_id AS delivered
FROM formula_drug drug
    JOIN valid_sheet_files vsf ON drug.sheet_file_id = vsf.sheet_id
    JOIN formula_prescription pres ON pres.uuid_folio = drug.prescription_id;


 SELECT
    sheetfile.id AS sheetfile_id,
    datafile.entity_id
    FROM
        inai_sheetfile sheetfile
        JOIN inai_datafile datafile ON sheetfile.data_file_id = datafile.id
    WHERE
        sheetfile.behavior_id::text = 'need_merge'::text OR sheetfile.behavior_id::text = 'merged'::text;


-- valid_sheet_files
SELECT sf.id AS sheet_id,
    datafile.entity_id
   FROM inai_sheetfile sf
     JOIN inai_datafile datafile ON sf.data_file_id = datafile.id
  WHERE sf.behavior_id::text <> 'invalid'::text;


SELECT
    delivered_final_id,
    COUNT(delivered_final_id) AS total
FROM formula_prescription
GROUP BY delivered_final_id;

