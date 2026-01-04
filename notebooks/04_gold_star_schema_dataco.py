# Databricks notebook source
# 03_gold_star_schema_dataco (PURE PYTHON VERSION - runnable)
# Run in a Databricks Python notebook cell(s)

def run(sql_text: str):
    return spark.sql(sql_text)

# 1) Create schema
run("CREATE SCHEMA IF NOT EXISTS gold")

# 2) Dimensions
run("""
CREATE OR REPLACE TABLE gold.dim_date AS
WITH bounds AS (
  SELECT
    LEAST(MIN(order_date), MIN(ship_date)) AS min_date,
    GREATEST(MAX(order_date), MAX(ship_date)) AS max_date
  FROM silver.dataco_supplychain_clean
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
FROM dates
""")

run("""
CREATE OR REPLACE TABLE gold.dim_customer AS
SELECT DISTINCT
  customer_id,
  customer_segment,
  customer_country,
  customer_state,
  customer_city,
  customer_zipcode,
  latitude,
  longitude
FROM silver.dataco_supplychain_clean
""")

run("""
CREATE OR REPLACE TABLE gold.dim_product AS
SELECT DISTINCT
  product_card_id,
  product_name,
  product_category_id,
  category_id,
  department_id,
  catalog_price,
  product_description,
  product_status
FROM silver.dataco_supplychain_clean
""")

# Category/Department dims rely on name columns in Bronze.
run("""
CREATE OR REPLACE TABLE gold.dim_category AS
SELECT DISTINCT
  category_id,
  category_name
FROM bronze.dataco_supplychain_raw
""")

run("""
CREATE OR REPLACE TABLE gold.dim_department AS
SELECT DISTINCT
  department_id,
  department_name
FROM bronze.dataco_supplychain_raw
""")

# 3) Fact
run("""
CREATE OR REPLACE TABLE gold.fact_order_item AS
SELECT
  order_item_id,
  order_id,
  customer_id,
  product_card_id,
  category_id,
  department_id,

  CAST(date_format(order_date, 'yyyyMMdd') AS INT) AS order_date_key,
  CAST(date_format(ship_date,  'yyyyMMdd') AS INT) AS ship_date_key,

  gross_sales,
  net_sales,
  discount_amount,
  discount_rate,
  profit,
  quantity,
  unit_price,

  days_for_shipping_real,
  days_for_shipment_scheduled,
  late_delivery_risk,
  is_late_by_days,

  delivery_status,
  shipping_mode,
  order_status,
  market,
  order_region,
  order_country,
  order_state,
  order_city,
  order_zipcode,

  _ingest_ts,
  _batch_id
FROM silver.dataco_supplychain_clean
""")

# 4) Validations
display(run("""
SELECT
  (SELECT COUNT(*) FROM silver.dataco_supplychain_clean) AS silver_rows,
  (SELECT COUNT(*) FROM gold.fact_order_item)            AS fact_rows
"""))

display(run("""
SELECT
  SUM(CASE WHEN d1.customer_id IS NULL THEN 1 ELSE 0 END)     AS missing_customer_dim,
  SUM(CASE WHEN d2.product_card_id IS NULL THEN 1 ELSE 0 END) AS missing_product_dim,
  COUNT(*) AS fact_rows
FROM gold.fact_order_item f
LEFT JOIN gold.dim_customer d1 ON f.customer_id = d1.customer_id
LEFT JOIN gold.dim_product  d2 ON f.product_card_id = d2.product_card_id
"""))

display(run("""
SELECT
  SUM(CASE WHEN d.date_key IS NULL THEN 1 ELSE 0 END) AS missing_order_date_key,
  COUNT(*) AS fact_rows
FROM gold.fact_order_item f
LEFT JOIN gold.dim_date d ON f.order_date_key = d.date_key
"""))

display(run("""
SELECT
  SUM(CASE WHEN d.date_key IS NULL THEN 1 ELSE 0 END) AS missing_ship_date_key,
  COUNT(*) AS fact_rows
FROM gold.fact_order_item f
LEFT JOIN gold.dim_date d ON f.ship_date_key = d.date_key
"""))
