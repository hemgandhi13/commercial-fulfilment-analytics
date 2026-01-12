CREATE OR REPLACE TABLE workspace.silver.dataco_supplychain_clean_v2 AS
WITH base AS (
  SELECT * FROM workspace.silver.dataco_supplychain_clean
),
canon AS (
  SELECT
    b.*,

    regexp_replace(trim(b.order_region),  '\\s+', ' ') AS order_region_std,
    regexp_replace(trim(b.market),        '\\s+', ' ') AS market_std,
    regexp_replace(trim(b.shipping_mode), '\\s+', ' ') AS shipping_mode_std,

    regexp_replace(trim(b.order_country), '\\s+', ' ') AS order_country_std,
    regexp_replace(trim(b.order_state),   '\\s+', ' ') AS order_state_std,
    regexp_replace(trim(b.order_city),    '\\s+', ' ') AS order_city_std,
    CAST(b.order_zipcode AS STRING)                    AS order_zipcode_std,

    regexp_replace(trim(b.customer_country), '\\s+', ' ') AS customer_country_std,
    regexp_replace(trim(b.customer_state),   '\\s+', ' ') AS customer_state_std,
    regexp_replace(trim(b.customer_city),    '\\s+', ' ') AS customer_city_std,
    CAST(b.customer_zipcode AS STRING)                    AS customer_zipcode_std

  FROM base b
),
norm AS (
  SELECT
    c.*,

    -- Country canonicalisation (USA variants)
    CASE
      WHEN c.order_country_std IN ('EE. UU.', 'EE.UU.', 'EE UU', 'ESTADOS UNIDOS', 'Estados Unidos', 'United States', 'USA')
        THEN 'USA'
      ELSE upper(regexp_replace(regexp_replace(c.order_country_std, '[^\\p{L}\\p{N} ]', ''), '\\s+', ' '))
    END AS order_country_key,

    upper(regexp_replace(regexp_replace(c.order_state_std, '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS order_state_key,
    upper(regexp_replace(regexp_replace(c.order_city_std,  '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS order_city_key,
    upper(regexp_replace(regexp_replace(coalesce(c.order_zipcode_std,''), '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS order_zipcode_key,

    CASE
      WHEN c.customer_country_std IN ('EE. UU.', 'EE.UU.', 'EE UU', 'ESTADOS UNIDOS', 'Estados Unidos', 'United States', 'USA')
        THEN 'USA'
      ELSE upper(regexp_replace(regexp_replace(c.customer_country_std, '[^\\p{L}\\p{N} ]', ''), '\\s+', ' '))
    END AS customer_country_key,

    upper(regexp_replace(regexp_replace(c.customer_state_std, '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS customer_state_key,
    upper(regexp_replace(regexp_replace(c.customer_city_std,  '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS customer_city_key,
    upper(regexp_replace(regexp_replace(coalesce(c.customer_zipcode_std,''), '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS customer_zipcode_key,

    upper(regexp_replace(regexp_replace(c.market_std,        '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS market_key,
    upper(regexp_replace(regexp_replace(c.order_region_std,  '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS order_region_key,
    upper(regexp_replace(regexp_replace(c.shipping_mode_std, '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS shipping_mode_key

  FROM canon c
)
SELECT * FROM norm;
