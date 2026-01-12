CREATE OR REPLACE TABLE workspace.silver.dataco_supplychain_clean_v3 AS
WITH s AS (
  SELECT * FROM workspace.silver.dataco_supplychain_clean_v2
),
fx_country AS (
  SELECT bad_value, good_value
  FROM workspace.silver.ref_text_fixes
  WHERE field = 'country'
),
fx_city AS (
  SELECT bad_value, good_value
  FROM workspace.silver.ref_text_fixes
  WHERE field = 'city'
)
SELECT
  s.*,

  -- Clean display fields (order)
  COALESCE(fc.good_value,  s.order_country_std) AS order_country_clean,
  COALESCE(fci.good_value, s.order_city_std)    AS order_city_clean,

  -- Clean display fields (customer)
  COALESCE(fcc.good_value,    s.customer_country_std) AS customer_country_clean,
  COALESCE(fccity.good_value, s.customer_city_std)    AS customer_city_clean,

  -- Keys derived from clean display fields 
  upper(regexp_replace(regexp_replace(COALESCE(fc.good_value, s.order_country_std),   '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS order_country_clean_key,
  upper(regexp_replace(regexp_replace(COALESCE(fci.good_value, s.order_city_std),     '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS order_city_clean_key,

  upper(regexp_replace(regexp_replace(COALESCE(fcc.good_value, s.customer_country_std),'[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS customer_country_clean_key,
  upper(regexp_replace(regexp_replace(COALESCE(fccity.good_value, s.customer_city_std),'[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS customer_city_clean_key

FROM s
LEFT JOIN fx_country fc    ON s.order_country_std    = fc.bad_value
LEFT JOIN fx_city    fci   ON s.order_city_std       = fci.bad_value
LEFT JOIN fx_country fcc   ON s.customer_country_std = fcc.bad_value
LEFT JOIN fx_city    fccity ON s.customer_city_std   = fccity.bad_value;
