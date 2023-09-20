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


SELECT
	rx.delivered_final_id,
	rx.iso_year,
	rx.iso_week,
	COUNT(*),
	SUM (drug.prescribed_amount) as prescribed,
	SUM (drug.delivered_amount) as delivered
FROM fm_55_201907_rx rx
JOIN fm_55_201907_drug drug ON rx.uuid_folio = drug.rx_id
GROUP BY
	rx.delivered_final_id,
	rx.iso_year,
	rx.iso_week;

