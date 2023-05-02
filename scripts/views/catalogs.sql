select
    presc.month,
    presc.entity_id,
    presc.iso_year,
    count(distinct presc.folio_ocamis) as folios_ocamis,
    count(distinct presc.folio_document) as folios_document,
    count(*) as prescriptions
from formula_prescription presc
group by presc.month, presc.entity_id, presc.iso_year;


SELECT
    COUNT(Distinct repeat_folios.uuid_folio) as folios_ocamis,
    sheet.id as sheet_id
FROM
    formula_drug drug
    JOIN inai_sheetfile sheet ON drug.sheet_file_id = sheet.id
    INNER JOIN (
        SELECT
            pres.uuid_folio as uuid_folio,
            pres.folio_ocamis as folio_ocamis
        FROM
            formula_prescription pres
        WHERE pres.folio_ocamis IN (
            SELECT folio_ocamis
            FROM formula_prescription
            GROUP BY folio_ocamis
            HAVING COUNT(uuid_folio) > 1
        )
        ORDER BY pres.folio_ocamis
    ) as repeat_folios
    ON drug.prescription_id = repeat_folios.uuid_folio
WHERE
    sheet.id = 1
GROUP BY sheet_id;

SELECT
    ent.id AS entity_id,
    presc.iso_year,
    presc.iso_week,
    sheet.id AS sheet_id,
    COUNT(drug.uuid) AS drug_count
FROM
    geo_entity ent
    JOIN formula_prescription presc ON ent.id = presc.entity_id
    JOIN formula_drug drug ON presc.uuid_folio = drug.prescription_id
    JOIN inai_sheetfile sheet ON drug.sheet_file_id = sheet.id
GROUP BY
    ent.id,
    presc.iso_year,
    presc.iso_week,
    sheet_id
ORDER BY
    ent.id,
    presc.iso_year,
    presc.iso_week,
    drug_count DESC;


SELECT
    pres.iso_year,
    pres.iso_week,
    drug.sheet_file_id AS sheet_id,
    pres.folio_ocamis as folio_ocamis,
    pres.doctor_id as doctor_id,
    pres.date_delivery as date_delivery,
    pres.date_release as date_release,
    drug.medicament_id as medicament_id
FROM
    formula_prescription pres
    JOIN formula_drug drug ON pres.uuid_folio = drug.prescription_id
WHERE
    pres.entity_id = 53 AND pres.iso_year = 2017 AND pres.iso_week = 49
ORDER BY
    folio_ocamis;


select mu.delegation_name
from med_cat_medicalunit mu

where
    mu.delegation_name is not null
    and mu.delegation_id is null
group by mu.delegation_name;



