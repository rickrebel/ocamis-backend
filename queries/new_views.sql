SELECT
    formula_drug.prescription_id as uuid,
    formula_prescription.folio_ocamis,
    formula_drug.lap_sheet_id,
    formula_drug.sheet_file_id
FROM formula_drug
JOIN formula_prescription
    ON formula_drug.prescription_id = formula_prescription.uuid;