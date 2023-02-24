view
SELECT concat(rec.week, '-', rec.year, '-', med_cat.key2, '-', clues.state_id, '-', med.delivered) AS unique_id,
    rec.week,
    rec.year,
    med_cat.key2,
    med_cat.comp_id,
    med_cat.comp_name,
    clues.state_id,
    med.delivered,
    count(*) AS count_medic,
    sum(med.prescrita) AS sum_presc
   FROM ( SELECT desabasto_recipereport2.folio_ocamis,
            desabasto_recipereport2.iso_year AS year,
            desabasto_recipereport2.iso_week AS week,
            desabasto_recipereport2.clues_id
           FROM desabasto_recipereport2) rec
     JOIN ( SELECT desabasto_recipemedicine2.clave_medicamento AS med_key,
            desabasto_recipemedicine2.prescribed_amount AS prescrita,
            desabasto_recipemedicine2.delivered,
            desabasto_recipemedicine2.recipe_id
           FROM desabasto_recipemedicine2) med ON med.recipe_id::text = rec.folio_ocamis::text
     JOIN ( SELECT component.id AS comp_id,
            component.name AS comp_name,
            present.id AS present_id,
            container.key2
           FROM desabasto_container container
             JOIN ( SELECT desabasto_presentation.id,
                    desabasto_presentation.description,
                    desabasto_presentation.component_id
                   FROM desabasto_presentation) present ON present.id = container.presentation_id
             JOIN ( SELECT desabasto_component.id,
                    desabasto_component.name
                   FROM desabasto_component) component ON component.id = present.component_id) med_cat ON med_cat.key2::text = med.med_key::text
     JOIN ( SELECT desabasto_clues.id AS clues_id,
            desabasto_clues.state_id
           FROM desabasto_clues
          WHERE desabasto_clues.clues IS NOT NULL) clues ON clues.clues_id = rec.clues_id
  GROUP BY rec.week, rec.year, med.med_key, med_cat.key2, med_cat.comp_id, med_cat.comp_name, med_cat.present_desc, clues.state_id, med.delivered