SELECT
    comp.id as component_id,
    comp.priority as priority,
    comp.name as component,
    pres.description as presentation,
    pres.id as presentation_id,
    cont.name as container,
    cont.key as key,
    cont.key2 as key2,
    cont.id as container_id
FROM medicine_component comp
JOIN medicine_presentation pres ON pres.component_id = comp.id
JOIN medicine_container cont ON cont.presentation_id = pres.id;



