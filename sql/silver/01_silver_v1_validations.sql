-- A) Row counts: Bronze audited vs Silver v1
SELECT
  (SELECT COUNT(*) FROM workspace.bronze.dataco_supplychain_raw_audited) AS bronze_audited_rows,
  (SELECT COUNT(*) FROM workspace.silver.dataco_supplychain_clean)       AS silver_v1_rows;

-- B) Timestamp parse nulls (should be near 0)
SELECT
  SUM(CASE WHEN order_ts IS NULL THEN 1 ELSE 0 END) AS order_ts_nulls,
  SUM(CASE WHEN ship_ts  IS NULL THEN 1 ELSE 0 END) AS ship_ts_nulls,
  COUNT(*) AS total_rows
FROM workspace.silver.dataco_supplychain_clean;

-- C) Key nulls
SELECT
  SUM(CASE WHEN order_item_id   IS NULL THEN 1 ELSE 0 END) AS null_order_item_id,
  SUM(CASE WHEN order_id        IS NULL THEN 1 ELSE 0 END) AS null_order_id,
  SUM(CASE WHEN customer_id     IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
  SUM(CASE WHEN product_card_id IS NULL THEN 1 ELSE 0 END) AS null_product_card_id
FROM workspace.silver.dataco_supplychain_clean;

-- D) Grain uniqueness check
SELECT
  COUNT(*) AS rows,
  COUNT(DISTINCT order_item_id) AS distinct_order_item_id
FROM workspace.silver.dataco_supplychain_clean;

-- E) Commercial sanity checks
SELECT
  MIN(discount_rate) AS min_discount_rate,
  MAX(discount_rate) AS max_discount_rate,
  MIN(net_sales)     AS min_net_sales,
  MIN(gross_sales)   AS min_gross_sales,
  MIN(profit)        AS min_profit
FROM workspace.silver.dataco_supplychain_clean;
