CREATE SCHEMA IF NOT EXISTS workspace.silver;


CREATE OR REPLACE TABLE workspace.silver.dataco_supplychain_clean AS
WITH src AS (
  SELECT *
  FROM workspace.bronze.dataco_supplychain_raw_audited
),
parsed AS (
  SELECT
    src.*,
    COALESCE(
      to_timestamp(order_date_dateorders,   'M/d/yyyy H:mm'),
      to_timestamp(order_date_dateorders,   'MM/dd/yyyy HH:mm')
    ) AS order_ts_parsed,
    COALESCE(
      to_timestamp(shipping_date_dateorders,'M/d/yyyy H:mm'),
      to_timestamp(shipping_date_dateorders,'MM/dd/yyyy HH:mm')
    ) AS ship_ts_parsed
  FROM src
)
SELECT
  CAST(order_item_id AS BIGINT) AS order_item_id,
  CAST(order_id      AS BIGINT) AS order_id,
  CAST(customer_id   AS BIGINT) AS customer_id,
  CAST(product_card_id AS BIGINT) AS product_card_id,
  CAST(category_id     AS BIGINT) AS category_id,
  CAST(department_id   AS BIGINT) AS department_id,

  order_date_dateorders    AS order_ts_raw,
  shipping_date_dateorders AS ship_ts_raw,

  order_ts_parsed AS order_ts,
  ship_ts_parsed  AS ship_ts,

  to_date(order_ts_parsed) AS order_date,
  to_date(ship_ts_parsed)  AS ship_date,

  CAST(sales                    AS DOUBLE) AS gross_sales,
  CAST(order_item_total         AS DOUBLE) AS net_sales,
  CAST(order_item_discount      AS DOUBLE) AS discount_amount,
  CAST(order_item_discount_rate AS DOUBLE) AS discount_rate,
  CAST(order_profit_per_order   AS DOUBLE) AS profit,

  CAST(order_item_quantity      AS INT)    AS quantity,
  CAST(order_item_product_price AS DOUBLE) AS unit_price,
  CAST(product_price            AS DOUBLE) AS catalog_price,

  CAST(days_for_shipping_real        AS INT) AS days_for_shipping_real,
  CAST(days_for_shipment_scheduled   AS INT) AS days_for_shipment_scheduled,
  CAST(late_delivery_risk            AS INT) AS late_delivery_risk,

  CAST(delivery_status AS STRING) AS delivery_status,
  CAST(shipping_mode   AS STRING) AS shipping_mode,
  CAST(order_status    AS STRING) AS order_status,

  CAST(market      AS STRING) AS market,
  CAST(order_region AS STRING) AS order_region,

  CAST(order_country AS STRING) AS order_country,
  CAST(order_state   AS STRING) AS order_state,
  CAST(order_city    AS STRING) AS order_city,
  CAST(order_zipcode AS STRING) AS order_zipcode,

  CAST(customer_segment AS STRING) AS customer_segment,
  CAST(customer_country AS STRING) AS customer_country,
  CAST(customer_state   AS STRING) AS customer_state,
  CAST(customer_city    AS STRING) AS customer_city,
  CAST(customer_zipcode AS STRING) AS customer_zipcode,

  CAST(latitude  AS DOUBLE) AS latitude,
  CAST(longitude AS DOUBLE) AS longitude,

  CAST(product_name        AS STRING) AS product_name,
  CAST(product_category_id AS BIGINT) AS product_category_id,
  CAST(product_description AS STRING) AS product_description,
  CAST(product_status      AS BIGINT) AS product_status,

  CASE WHEN days_for_shipping_real > days_for_shipment_scheduled THEN 1 ELSE 0 END AS is_late_by_days,

  _ingest_ts,
  _batch_id

FROM parsed;
