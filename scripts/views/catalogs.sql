select
    rx.month,
    rx.entity_id,
    rx.iso_year,
    count(distinct rx.folio_ocamis) as folios_ocamis,
    count(distinct rx.folio_document) as folios_document,
    count(*) as prescriptions
from formula_rx rx
group by rx.month, rx.entity_id, rx.iso_year;


SELECT
    COUNT(Distinct repeat_folios.uuid_folio) as folios_ocamis,
    sheet.id as sheet_id
FROM
    formula_drug drug
    JOIN inai_sheetfile sheet ON drug.sheet_file_id = sheet.id
    INNER JOIN (
        SELECT
            rx.uuid_folio as uuid_folio,
            rx.folio_ocamis as folio_ocamis
        FROM
            formula_rx rx
        WHERE rx.folio_ocamis IN (
            SELECT folio_ocamis
            FROM formula_rx
            GROUP BY folio_ocamis
            HAVING COUNT(uuid_folio) > 1
        )
        ORDER BY rx.folio_ocamis
    ) as repeat_folios
    ON drug.rx_id = repeat_folios.uuid_folio
WHERE
    sheet.id = 1
GROUP BY sheet_id;

SELECT
    ent.id AS entity_id,
    rx.iso_year,
    rx.iso_week,
    sheet.id AS sheet_id,
    COUNT(drug.uuid) AS drugs_count
FROM
    geo_entity ent
    JOIN formula_rx rx ON ent.id = rx.entity_id
    JOIN formula_drug drug ON rx.uuid_folio = drug.rx_id
    JOIN inai_sheetfile sheet ON drug.sheet_file_id = sheet.id
GROUP BY
    ent.id,
    rx.iso_year,
    rx.iso_week,
    sheet_id
ORDER BY
    ent.id,
    rx.iso_year,
    rx.iso_week,
    drugs_count DESC;


SELECT
    rx.iso_year,
    rx.iso_week,
    drug.sheet_file_id AS sheet_id,
    rx.folio_ocamis as folio_ocamis,
    rx.doctor_id as doctor_id,
    rx.date_delivery as date_delivery,
    rx.date_release as date_release,
    drug.medicament_id as medicament_id
FROM
    formula_rx rx
    JOIN formula_drug drug ON rx.uuid_folio = drug.rx_id
WHERE
    rx.entity_id = 53 AND
    rx.iso_year = 2017 AND
    rx.iso_week = 49
ORDER BY
    folio_ocamis;


select mu.delegation_name
from med_cat_medicalunit mu

where
    mu.delegation_name is not null
    and mu.delegation_id is null
group by mu.delegation_name;



