SELECT
    inst.code AS code,
    ent.name AS entity_name,
    presc.iso_year,
    presc.month,
    deliv.name AS delivered_short_name,
    COUNT(drug.uuid) AS drug_count,
    SUM(drug.prescribed_amount) AS total_prescribed_amount,
    SUM(drug.delivered_amount) AS total_delivered_amount
FROM
    geo_entity ent
    JOIN geo_institution inst ON ent.institution_id = inst.id
    JOIN formula_prescription presc ON ent.id = presc.entity_id
    JOIN formula_drug drug ON presc.uuid_folio = drug.prescription_id
    JOIN med_cat_delivered deliv ON drug.delivered_id = deliv.hex_hash
GROUP BY
    ent.name,
    inst.code,
    presc.iso_year,
    presc.month,
    deliv.name
ORDER BY
    ent.name,
    inst.code,
    presc.iso_year,
    presc.month,
    deliv.name;


SELECT
    inst.code AS code,
    ent.name AS entity_name,
    presc.iso_year,
    presc.month,
    df.name AS delivered_short_name,
    COUNT(DISTINCT presc.uuid_folio) AS prescription_count,
    SUM(drug.prescribed_amount) AS total_prescribed_amount,
    SUM(drug.delivered_amount) AS total_delivered_amount
FROM
    geo_entity ent
    JOIN geo_institution inst ON ent.institution_id = inst.id
    JOIN formula_prescription presc ON ent.id = presc.entity_id
    JOIN formula_drug drug ON presc.uuid_folio = drug.prescription_id
    JOIN med_cat_delivered df ON presc.delivered_final_id = df.hex_hash
GROUP BY
    ent.name,
    inst.code,
    presc.iso_year,
    presc.month,
    df.name
ORDER BY
    ent.name,
    inst.code,
    presc.iso_year,
    presc.month,
    df.name;



SELECT
    inst.code AS code,
    ent.name AS entity_name,
    presc.iso_year,
    presc.month,
    df.name AS delivered_short_name,
    COUNT(presc.uuid_folio) AS prescription_count
FROM
    geo_entity ent
    JOIN geo_institution inst ON ent.institution_id = inst.id
    JOIN formula_prescription presc ON ent.id = presc.entity_id
    JOIN med_cat_delivered df ON presc.delivered_final_id = df.hex_hash
GROUP BY
    ent.name,
    inst.code,
    presc.iso_year,
    presc.month,
    df.name
ORDER BY
    ent.name,
    inst.code,
    presc.iso_year,
    presc.month,
    df.name;


