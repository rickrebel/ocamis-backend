-- drugs_and_rxs
 SELECT
    drug.sheet_file_id AS sheet_id,
    rx.entity_id,
    rx.folio_ocamis,
	rx.month,
	rx.iso_week,
	rx.iso_year,
    rx.uuid_folio,
    rx.delivered_final_id AS delivered
   FROM formula_rx rx
     JOIN formula_drug drug ON rx.uuid_folio = drug.rx_id;


-- drugs_and_rxs_valid
 SELECT vsf.sheet_id,
    vsf.entity_id,
    rx.folio_ocamis,
    rx.month,
    rx.iso_week,
    rx.iso_year,
    rx.uuid_folio,
    rx.delivered_final_id AS delivered
FROM formula_drug drug
    JOIN valid_sheet_files vsf ON drug.sheet_file_id = vsf.sheet_id
    JOIN formula_rx rx ON rx.uuid_folio = drug.rx_id;


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
FROM formula_rx
GROUP BY delivered_final_id;


SELECT * FROM public.formula_rx
WHERE uuid_folio = '53216182-a857-4d53-b4b5-b952428806e7';


SELECT * FROM public.formula_rx
WHERE iso_year = 2017 AND iso_week = 26 AND iso_delegation = 325 AND month = 6 and iso_year = 2017
LIMIT 400;

DELETE FROM public.formula_rx
WHERE iso_year = 2017 AND iso_week = 26 AND iso_delegation = 325 AND month = 6;

DELETE FROM public.formula_drug
WHERE rx_id IN ('002c045e-9579-4eba-950d-def58dfca681', '003fc78b-c0e5-4d1d-968c-cb3fc181d541');

SELECT * FROM public.formula_drug
WHERE rx_id IN ('002c045e-9579-4eba-950d-def58dfca681', '003fc78b-c0e5-4d1d-968c-cb3fc181d541');



CREATE INDEX if not exists same_name_index
ON fm_53_202301_rx(entity_id, iso_week, iso_year);


-- alter table formula_drug
-- add constraint formula_drug_pkey
-- primary key (uuid);

SELECT *
FROM formula_drug
WHERE uuid = 'e35bdaba-ad70-4318-8208-e82acd3936b2'
LIMIT 1;

-- alter table formula_rx
-- add constraint formula_rx_pkey
-- primary key (uuid_folio);

SELECT *
FROM formula_rx
WHERE uuid_folio = 'c3464ae7-5f49-4b65-ab05-1b187da40b6c'
LIMIT 1;


DELETE FROM formula_rx
WHERE entity_id = 55 AND year = 2018 AND month = 11
    AND iso_year = 2018 AND iso_week = 47 AND iso_delegation = 254;


DELETE FROM formula_rx
WHERE entity_id = 55 AND year = 2018 AND month = 11
	AND iso_year = 2018 AND iso_week = 46 AND iso_delegation = 247;

DELETE FROM formula_drug
    WHERE entity_week_id IN (27686);


