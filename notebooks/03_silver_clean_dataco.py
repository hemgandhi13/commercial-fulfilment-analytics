# Databricks notebook source
# 02_silver_clean_dataco (PURE PYTHON VERSION - runnable)
# Run in a Databricks Python notebook cell(s)

def run(sql_text: str):
    return spark.sql(sql_text)

# 1) Create schema
run("CREATE SCHEMA IF NOT EXISTS silver")

# 2) Build table
run("""
CREATE OR REPLACE TABLE silver.dataco_supplychain_clean AS
SELECT
  CAST(order_item_id AS BIGINT)       AS order_item_id,
  CAST(order_id AS BIGINT)            AS order_id,
  CAST(customer_id AS BIGINT)         AS customer_id,
  CAST(product_card_id AS BIGINT)     AS product_card_id,
  CAST(category_id AS BIGINT)         AS category_id,
  CAST(department_id AS BIGINT)       AS department_id,

  order_date_dateorders               AS order_ts_raw,
  shipping_date_dateorders            AS ship_ts_raw,

  COALESCE(
    to_timestamp(order_date_dateorders,   'M/d/yyyy H:mm'),
    to_timestamp(order_date_dateorders,   'MM/dd/yyyy HH:mm'),
    to_timestamp(order_date_dateorders,   'M/d/yyyy H:mm:ss'),
    to_timestamp(order_date_dateorders,   'MM/dd/yyyy HH:mm:ss')
  ) AS order_ts,

  COALESCE(
    to_timestamp(shipping_date_dateorders,'M/d/yyyy H:mm'),
    to_timestamp(shipping_date_dateorders,'MM/dd/yyyy HH:mm'),
    to_timestamp(shipping_date_dateorders,'M/d/yyyy H:mm:ss'),
    to_timestamp(shipping_date_dateorders,'MM/dd/yyyy HH:mm:ss')
  ) AS ship_ts,

  to_date(
    COALESCE(
      to_timestamp(order_date_dateorders, 'M/d/yyyy H:mm'),
      to_timestamp(order_date_dateorders, 'MM/dd/yyyy HH:mm'),
      to_timestamp(order_date_dateorders, 'M/d/yyyy H:mm:ss'),
      to_timestamp(order_date_dateorders, 'MM/dd/yyyy HH:mm:ss')
    )
  ) AS order_date,

  to_date(
    COALESCE(
      to_timestamp(shipping_date_dateorders,'M/d/yyyy H:mm'),
      to_timestamp(shipping_date_dateorders,'MM/dd/yyyy HH:mm'),
      to_timestamp(shipping_date_dateorders,'M/d/yyyy H:mm:ss'),
      to_timestamp(shipping_date_dateorders,'MM/dd/yyyy HH:mm:ss')
    )
  ) AS ship_date,

  CAST(sales AS DOUBLE)                    AS gross_sales,
  CAST(order_item_total AS DOUBLE)         AS net_sales,
  CAST(order_item_discount AS DOUBLE)      AS discount_amount,
  CAST(order_item_discount_rate AS DOUBLE) AS discount_rate,
  CAST(order_profit_per_order AS DOUBLE)   AS profit,

  CAST(order_item_quantity AS INT)         AS quantity,
  CAST(order_item_product_price AS DOUBLE) AS unit_price,
  CAST(product_price AS DOUBLE)            AS catalog_price,

  CAST(days_for_shipping_real AS INT)      AS days_for_shipping_real,
  CAST(days_for_shipment_scheduled AS INT) AS days_for_shipment_scheduled,
  CAST(late_delivery_risk AS INT)          AS late_delivery_risk,
  delivery_status,
  shipping_mode,
  order_status,
  market,
  order_region,
  order_country,
  order_state,
  order_city,
  CAST(order_zipcode AS STRING)            AS order_zipcode,

  customer_segment,
  customer_country,
  customer_state,
  customer_city,
  CAST(customer_zipcode AS STRING)         AS customer_zipcode,
  CAST(latitude AS DOUBLE)                 AS latitude,
  CAST(longitude AS DOUBLE)                AS longitude,

  product_name,
  CAST(product_category_id AS BIGINT)      AS product_category_id,
  product_description,
  product_status,

  CASE WHEN days_for_shipping_real > days_for_shipment_scheduled THEN 1 ELSE 0 END AS is_late_by_days,

  _ingest_ts,
  _batch_id
FROM bronze.dataco_supplychain_raw_audited
""")

# 3) Validations (display results)
display(run("""
SELECT
  (SELECT COUNT(*) FROM bronze.dataco_supplychain_raw) AS bronze_rows,
  (SELECT COUNT(*) FROM silver.dataco_supplychain_clean) AS silver_rows
"""))

display(run("""
SELECT
  SUM(CASE WHEN order_ts IS NULL THEN 1 ELSE 0 END) AS order_ts_nulls,
  SUM(CASE WHEN ship_ts  IS NULL THEN 1 ELSE 0 END) AS ship_ts_nulls,
  COUNT(*) AS total_rows
FROM silver.dataco_supplychain_clean
"""))

display(run("""
SELECT
  SUM(CASE WHEN order_item_id IS NULL THEN 1 ELSE 0 END) AS null_order_item_id,
  SUM(CASE WHEN order_id      IS NULL THEN 1 ELSE 0 END) AS null_order_id,
  SUM(CASE WHEN customer_id   IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
  SUM(CASE WHEN product_card_id IS NULL THEN 1 ELSE 0 END) AS null_product_id
FROM silver.dataco_supplychain_clean
"""))

display(run("""
SELECT
  COUNT(*) AS rows,
  COUNT(DISTINCT order_item_id) AS distinct_order_item_id
FROM silver.dataco_supplychain_clean
"""))

display(run("""
SELECT
  MIN(discount_rate) AS min_discount_rate,
  MAX(discount_rate) AS max_discount_rate,
  MIN(net_sales)     AS min_net_sales,
  MIN(gross_sales)   AS min_gross_sales,
  MIN(profit)        AS min_profit
FROM silver.dataco_supplychain_clean
"""))

display(run("""
SELECT
  SUM(CASE WHEN ship_date < order_date THEN 1 ELSE 0 END) AS ship_before_order_rows,
  SUM(CASE WHEN quantity <= 0 THEN 1 ELSE 0 END)          AS nonpositive_qty_rows,
  SUM(CASE WHEN unit_price < 0 THEN 1 ELSE 0 END)         AS negative_unit_price_rows
FROM silver.dataco_supplychain_clean
"""))
