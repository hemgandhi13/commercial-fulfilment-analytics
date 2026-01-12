-- A) Row count must remain stable across v1/v2/v3
SELECT
  (SELECT COUNT(*) FROM workspace.silver.dataco_supplychain_clean)     AS v1_rows,
  (SELECT COUNT(*) FROM workspace.silver.dataco_supplychain_clean_v2)  AS v2_rows,
  (SELECT COUNT(*) FROM workspace.silver.dataco_supplychain_clean_v3)  AS v3_rows;

-- B) Encoding corruption after mapping (goal: zero or near-zero)
SELECT
  SUM(CASE WHEN order_country_clean LIKE '%�%' THEN 1 ELSE 0 END) AS bad_order_country_after,
  SUM(CASE WHEN order_city_clean    LIKE '%�%' THEN 1 ELSE 0 END) AS bad_order_city_after,
  SUM(CASE WHEN customer_country_clean LIKE '%�%' THEN 1 ELSE 0 END) AS bad_customer_country_after,
  SUM(CASE WHEN customer_city_clean    LIKE '%�%' THEN 1 ELSE 0 END) AS bad_customer_city_after,
  COUNT(*) AS total_rows
FROM workspace.silver.dataco_supplychain_clean_v3;

-- C) Grain uniqueness
SELECT COUNT(*) AS rows, COUNT(DISTINCT order_item_id) AS distinct_order_item_id
FROM workspace.silver.dataco_supplychain_clean_v3;

-- D) Key nulls
SELECT
  SUM(CASE WHEN order_item_id   IS NULL THEN 1 ELSE 0 END) AS null_order_item_id,
  SUM(CASE WHEN order_id        IS NULL THEN 1 ELSE 0 END) AS null_order_id,
  SUM(CASE WHEN customer_id     IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
  SUM(CASE WHEN product_card_id IS NULL THEN 1 ELSE 0 END) AS null_product_card_id
FROM workspace.silver.dataco_supplychain_clean_v3;
