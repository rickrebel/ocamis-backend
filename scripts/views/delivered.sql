SELECT
    inst.code AS code,
    ent.name AS entity_name,
    rx.iso_year,
    rx.month,
    deliv.name AS delivered_short_name,
    COUNT(drug.uuid) AS drug_count,
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


