CREATE MATERIALIZED VIEW recipes_by_week_state AS
SELECT

  concat()

  concat(customers.id, '-', orders.id) AS unique_id,
  concat(customers.first_name,' ', customers.last_name) AS customer_name, 
  orders.created_on AS purchase_date,
  addresses.city AS city,
  addresses.state AS state,
  count(products.product_name) AS order_size,
  sum(products.product_cost) AS order_cost
FROM orders

  

  INNER JOIN customers ON orders.customer_id = customers.id
  INNER JOIN products_orders po ON orders.id = po.order_id
  INNER JOIN products ON po.product_id = products.id
  INNER JOIN addresses ON addresses.customer_id = orders.customer_id
GROUP BY customer_name, purchase_date, city, state;


SELECT * FROM 
(SELECT id, short_name
FROM desabasto_state
WHERE desabasto_state.code_name IS NOT NULL) state



SELECT COUNT(*), clues.state_id, state.short_name
FROM desabasto_clues as clues
JOIN (SELECT id, short_name
FROM desabasto_state
WHERE desabasto_state.code_name IS NOT NULL) as state ON state.id = clues.state_id
GROUP BY clues.state_id, state.short_name



-- View: public.originvslanded_without_guest

-- DROP VIEW public.originvslanded_without_guest;

CREATE OR REPLACE VIEW public.originvslanded_without_guest AS 
 SELECT mi_tabla.originname,
        CASE mi_tabla.landed
            WHEN true THEN 'VERDADERO'::text
            WHEN false THEN 'FALSO'::text
            ELSE 'NULO'::text
        END AS landed_case,
    count(*) AS count
   FROM ( SELECT 1,
            oref.id,
            oref.name,
            oref.clave,
            oref.name AS originname,
            2,
            um.id,
            um."idMessenger",
            um.page,
            um.user_id,
            um."statusMess",
            um."deletConfirmation",
            um.instructions,
            um."howComment",
            um.text_response,
            um."pageP_id",
            um.last_interaction,
            um.last_notify,
            um.checking_date,
            um.checking_lapse,
            um.interest_current,
            um.interest_degree,
            um.reputation,
            um.push_suscription,
            um.extra_data,
            um.payload_response,
            um.subscribe,
            3,
            mref.id,
            mref.is_landed,
            mref.ref_raw,
            mref.created,
            mref.guest_id,
            mref.message_payload_id,
            mref.origin_id,
            mref."userMessenger_id",
            mref.is_landed AS landed
           FROM core_usermessenger um
             LEFT JOIN fb_messenger_messengerreference mref ON mref."userMessenger_id" = um.id
             LEFT JOIN fb_messenger_origin_ref oref ON oref.id = mref.origin_id
          WHERE um."pageP_id" = 37 AND mref.guest_id IS NULL) mi_tabla("?column?", id, name, clave, originname, "?column?_1", id_1, "idMessenger", page, user_id, "statusMess", "deletConfirmation", instructions, "howComment", text_response, "pageP_id", last_interaction, last_notify, checking_date, checking_lapse, interest_current, interest_degree, reputation, push_suscription, extra_data, payload_response, subscribe, "?column?_2", id_2, is_landed, ref_raw, created, guest_id, message_payload_id, origin_id, "userMessenger_id", landed)
  GROUP BY mi_tabla.originname, mi_tabla.landed
  ORDER BY mi_tabla.originname;

ALTER TABLE public.originvslanded_without_guest
  OWNER TO user_yeeko;



  -- View: public.usuariosmessenger_si_estan_en_alertas

-- DROP VIEW public.usuariosmessenger_si_estan_en_alertas;

CREATE OR REPLACE VIEW public.usuariosmessenger_si_estan_en_alertas AS 
 SELECT total.user_messenger
   FROM ( SELECT user_messenger_in_liga.user_messenger
           FROM fb_messenger_sentalert
             JOIN user_messenger_in_liga ON fb_messenger_sentalert."userMessenger_id" = user_messenger_in_liga.user_messenger
          GROUP BY user_messenger_in_liga.user_messenger) total;

ALTER TABLE public.usuariosmessenger_si_estan_en_alertas
  OWNER TO user_yeeko;



SELECT user_messenger_in_liga.user_messenger
           FROM fb_messenger_sentalert
             JOIN user_messenger_in_liga ON fb_messenger_sentalert."userMessenger_id" = user_messenger_in_liga.user_messenger
          GROUP BY user_messenger_in_liga.user_messenger



SELECT 
  concat(clues.state_id, clues.institution_id) AS unique_id,
  clues.state_id,
  state.short_name AS state_name,
  clues.institution_id,
  COUNT(*) AS counter

  FROM desabasto_clues AS clues
    INNER JOIN (
      SELECT id, short_name
      FROM desabasto_state
      ) AS state 
        ON state.id = clues.state_id

GROUP BY clues.state_id, state.short_name, clues.institution_id
ORDER BY clues.state_id




SELECT concat(rec.week, '-', rec.year) AS unique_id, COUNT(*)
FROM (
  SELECT
    recipe.iso_week AS week,
    recipe.iso_year AS year
  FROM desabasto_recipereport2 AS recipe) AS rec
GROUP BY rec.week, rec.year
ORDER BY rec.week



SELECT
  concat(rec.week, '-', rec.year, '-', med_cat.key2, '-',
    clues.state_id, '-', med.delivered) AS unique_id,
  med_cat.key2,
  med_cat.comp_id,
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
  WHERE year_month = "2021-12") AS rec
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
      --present.description,
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
  med_cat.comp_id, clues.state_id, med.delivered;





SELECT 
  rec.year_month,
  rec.delivered,
  COUNT(*)
FROM (
  SELECT
    recipe.folio_ocamis AS folio_ocamis,
    recipe.iso_year AS year,
    recipe.iso_week AS week,
    recipe.year_month,
    recipe.delivered
  FROM desabasto_recipereport2 AS recipe) AS rec
GROUP BY rec.delivered, rec.year_month
ORDER BY rec.year_month, rec.delivered






SELECT 
  rec.year_month,
  rec.delivered,
  COUNT(*)
FROM (
  SELECT
    recipe.folio_ocamis AS folio_ocamis,
    recipe.iso_year AS year,
    recipe.iso_week AS week,
    recipe.year_month,
    recipe.delivered
  FROM desabasto_recipereport2 AS recipe) AS rec
GROUP BY rec.delivered, rec.year_month
ORDER BY rec.year_month, rec.delivered



