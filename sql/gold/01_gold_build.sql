-- ============================================================
-- 01_gold_build.sql
-- Gold star schema build (Databricks SQL / Delta)
-- Source: workspace.silver.dataco_supplychain_clean_current
-- ============================================================

CREATE SCHEMA IF NOT EXISTS workspace.gold;

-- ---------------------------
-- Optional clean reset
-- ---------------------------
DROP TABLE IF EXISTS workspace.gold.fact_sales;
DROP TABLE IF EXISTS workspace.gold.fact_fulfilment;

DROP TABLE IF EXISTS workspace.gold.dim_channel;
DROP TABLE IF EXISTS workspace.gold.dim_geo;
DROP TABLE IF EXISTS workspace.gold.dim_discount_band;

DROP TABLE IF EXISTS workspace.gold.dim_department;
DROP TABLE IF EXISTS workspace.gold.dim_category;
DROP TABLE IF EXISTS workspace.gold.dim_product;
DROP TABLE IF EXISTS workspace.gold.dim_customer;
DROP TABLE IF EXISTS workspace.gold.dim_date;

-- ============================================================
-- DIMENSIONS
-- ============================================================

-- dim_date (date spine)
CREATE OR REPLACE TABLE workspace.gold.dim_date
USING delta
AS
WITH bounds AS (
  SELECT
    LEAST(MIN(order_date), MIN(ship_date))  AS min_date,
    GREATEST(MAX(order_date), MAX(ship_date)) AS max_date
  FROM workspace.silver.dataco_supplychain_clean_current
),
dates AS (
  SELECT explode(sequence(min_date, max_date, interval 1 day)) AS date_day
  FROM bounds
)
SELECT
  CAST(date_format(date_day, 'yyyyMMdd') AS INT) AS date_key,
  date_day                                     AS date,
  year(date_day)                               AS year,
  quarter(date_day)                            AS quarter,
  month(date_day)                              AS month,
  date_format(date_day, 'yyyy-MM')             AS year_month,
  weekofyear(date_day)                         AS week_of_year,
  date_format(date_day, 'EEEE')                AS day_name,
  dayofweek(date_day)                          AS day_of_week
FROM dates;

-- dim_customer
CREATE OR REPLACE TABLE workspace.gold.dim_customer
USING delta
AS
SELECT DISTINCT
  customer_id,
  customer_segment,
  customer_country,
  customer_state,
  customer_city,
  customer_zipcode,
  latitude,
  longitude,
  customer_country_key,
  customer_state_key,
  customer_city_key,
  customer_zipcode_key
FROM workspace.silver.dataco_supplychain_clean_current;

-- dim_product
CREATE OR REPLACE TABLE workspace.gold.dim_product
USING delta
AS
SELECT DISTINCT
  product_card_id,
  product_name,
  product_category_id,
  category_id,
  department_id,
  catalog_price,
  product_description,
  product_status
FROM workspace.silver.dataco_supplychain_clean_current;

-- dim_category
-- NOTE: This assumes category_name exists in your bronze audited table.
-- If it does not, either:
--   (a) add category_name into Silver, or
--   (b) keep only category_id in this dimension.
CREATE OR REPLACE TABLE workspace.gold.dim_category
USING delta
AS
SELECT DISTINCT
  category_id,
  category_name
FROM workspace.bronze.dataco_supplychain_raw_audited
WHERE category_id IS NOT NULL;

-- dim_department
CREATE OR REPLACE TABLE workspace.gold.dim_department
USING delta
AS
SELECT DISTINCT
  department_id,
  department_name
FROM workspace.bronze.dataco_supplychain_raw_audited
WHERE department_id IS NOT NULL;

-- dim_geo (country/state/city grain; zipcode NOT required)
CREATE OR REPLACE TABLE workspace.gold.dim_geo
USING delta
AS
SELECT DISTINCT
  xxhash64(
    coalesce(order_country_key,''),
    coalesce(order_state_key,''),
    coalesce(order_city_key,'')
  ) AS geo_key,
  order_country AS country,
  order_state   AS state,
  order_city    AS city
FROM workspace.silver.dataco_supplychain_clean_current;

-- dim_channel (market/region/shipping_mode)
CREATE OR REPLACE TABLE workspace.gold.dim_channel
USING delta
AS
SELECT DISTINCT
  xxhash64(
    coalesce(market_key,''),
    coalesce(order_region_key,''),
    coalesce(shipping_mode_key,'')
  ) AS channel_key,
  market,
  order_region,
  shipping_mode,
  market_key,
  order_region_key,
  shipping_mode_key
FROM workspace.silver.dataco_supplychain_clean_current;

-- dim_discount_band (optional, useful for PBI slicing)
CREATE OR REPLACE TABLE workspace.gold.dim_discount_band
USING delta
AS
SELECT * FROM VALUES
  (1, '0% (No Discount)',      CAST(0.00 AS DOUBLE), CAST(0.00 AS DOUBLE)),
  (2, '>0% to 5%',             CAST(0.00 AS DOUBLE), CAST(0.05 AS DOUBLE)),
  (3, '>5% to 10%',            CAST(0.05 AS DOUBLE), CAST(0.10 AS DOUBLE)),
  (4, '>10% to 15%',           CAST(0.10 AS DOUBLE), CAST(0.15 AS DOUBLE)),
  (5, '>15% to 20%',           CAST(0.15 AS DOUBLE), CAST(0.20 AS DOUBLE)),
  (6, '>20% to 25%',           CAST(0.20 AS DOUBLE), CAST(0.25 AS DOUBLE))
AS t(discount_band_key, discount_band_label, rate_min, rate_max);

-- ============================================================
-- FACTS (same grain: 1 row per order_item_id)
-- ============================================================

-- fact_sales
CREATE OR REPLACE TABLE workspace.gold.fact_sales
USING delta
AS
SELECT
  order_item_id,
  order_id,

  customer_id,
  product_card_id,
  category_id,
  department_id,

  CAST(date_format(order_date, 'yyyyMMdd') AS INT) AS order_date_key,

  xxhash64(
    coalesce(order_country_key,''),
    coalesce(order_state_key,''),
    coalesce(order_city_key,'')
  ) AS geo_key,

  xxhash64(
    coalesce(market_key,''),
    coalesce(order_region_key,''),
    coalesce(shipping_mode_key,'')
  ) AS channel_key,

  CASE
    WHEN discount_rate = 0 THEN 1
    WHEN discount_rate > 0 AND discount_rate <= 0.05 THEN 2
    WHEN discount_rate > 0.05 AND discount_rate <= 0.10 THEN 3
    WHEN discount_rate > 0.10 AND discount_rate <= 0.15 THEN 4
    WHEN discount_rate > 0.15 AND discount_rate <= 0.20 THEN 5
    WHEN discount_rate > 0.20 AND discount_rate <= 0.25 THEN 6
    ELSE NULL
  END AS discount_band_key,

  gross_sales,
  net_sales,
  discount_amount,
  discount_rate,
  profit,
  quantity,
  unit_price,

  order_status,

  _ingest_ts,
  _batch_id
FROM workspace.silver.dataco_supplychain_clean_current;

-- fact_fulfilment
CREATE OR REPLACE TABLE workspace.gold.fact_fulfilment
USING delta
AS
SELECT
  order_item_id,
  order_id,

  customer_id,
  product_card_id,
  category_id,
  department_id,

  CAST(date_format(order_date, 'yyyyMMdd') AS INT) AS order_date_key,
  CAST(date_format(ship_date,  'yyyyMMdd') AS INT) AS ship_date_key,

  xxhash64(
    coalesce(order_country_key,''),
    coalesce(order_state_key,''),
    coalesce(order_city_key,'')
  ) AS geo_key,

  xxhash64(
    coalesce(market_key,''),
    coalesce(order_region_key,''),
    coalesce(shipping_mode_key,'')
  ) AS channel_key,

  days_for_shipping_real,
  days_for_shipment_scheduled,
  (days_for_shipping_real - days_for_shipment_scheduled) AS shipping_days_variance,
  late_delivery_risk,
  is_late_by_days,

  delivery_status,
  shipping_mode,
  order_status,

  order_zipcode,

  _ingest_ts,
  _batch_id
FROM workspace.silver.dataco_supplychain_clean_current;
