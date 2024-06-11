SELECT
    formula_drug.rx_id as uuid,
    formula_rx.folio_ocamis,
    formula_drug.lap_sheet_id,
    formula_drug.sheet_file_id
FROM formula_drug
JOIN formula_rx
    ON formula_drug.rx_id = formula_rx.uuid;