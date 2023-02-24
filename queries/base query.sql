

SELECT
  concat(rec.week, '-', rec.year, '-', med_cat.key2, '-',
    clues.state_id, '-', med.delivered) AS unique_id,
  rec.week,
  rec.year,
  med_cat.key2,
  med_cat.comp_id,
  med_cat.comp_name,
  med_cat.present_desc,
  clues.state_id,
  med.delivered as delivered,
  COUNT(*) as count_medic,
  SUM(med.prescrita) as sum_presc
FROM (
  SELECT
    folio_ocamis AS folio_ocamis,
    iso_year AS year,
    iso_week AS week,
    clues_id
  FROM desabasto_recipereport2
  WHERE iso_week = 50) AS rec
  INNER JOIN (
    SELECT
      clave_medicamento AS med_key,
      prescribed_amount AS prescrita,
      delivered,
      recipe_id
    FROM desabasto_recipemedicine2
  ) as med
  ON med.recipe_id = rec.folio_ocamis
  INNER JOIN (
    SELECT
      component.id AS comp_id,
      component.name AS comp_name,
      present.id AS present_id,
      present.description AS present_desc,
      container.key2 as key2
      --container.name
    FROM desabasto_container as container
    INNER JOIN (
      SELECT 
        id,
        description,
        component_id
      FROM desabasto_presentation
    ) as present
    ON present.id = container.presentation_id
    INNER JOIN (
      SELECT 
        id,
        name
      FROM desabasto_component
    ) as component ON component.id = present.component_id 

  ) as med_cat
  ON med_cat.key2 = med.med_key  
  INNER JOIN (
    SELECT
      id as clues_id,
      state_id
    FROM desabasto_clues
    WHERE clues IS NOT NULL
  ) as clues
  ON clues.clues_id = rec.clues_id

GROUP BY rec.week, rec.year, med.med_key, med_cat.key2,
  med_cat.comp_id, med_cat.comp_name, med_cat.present_desc,
   clues.state_id, med.delivered



















