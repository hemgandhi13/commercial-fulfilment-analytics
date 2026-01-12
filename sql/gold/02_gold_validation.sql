-- ============================================================
-- 02_gold_validations.sql
-- Gold QA checks (run after build)
-- ============================================================

-- 1) Row counts
SELECT 'gold.dim_date' AS table_name, COUNT(*) AS rows FROM workspace.gold.dim_date UNION ALL
SELECT 'gold.dim_customer', COUNT(*) FROM workspace.gold.dim_customer UNION ALL
SELECT 'gold.dim_product', COUNT(*) FROM workspace.gold.dim_product UNION ALL
SELECT 'gold.dim_category', COUNT(*) FROM workspace.gold.dim_category UNION ALL
SELECT 'gold.dim_department', COUNT(*) FROM workspace.gold.dim_department UNION ALL
SELECT 'gold.dim_geo', COUNT(*) FROM workspace.gold.dim_geo UNION ALL
SELECT 'gold.dim_channel', COUNT(*) FROM workspace.gold.dim_channel UNION ALL
SELECT 'gold.dim_discount_band', COUNT(*) FROM workspace.gold.dim_discount_band UNION ALL
SELECT 'gold.fact_sales', COUNT(*) FROM workspace.gold.fact_sales UNION ALL
SELECT 'gold.fact_fulfilment', COUNT(*) FROM workspace.gold.fact_fulfilment;

-- 2) Dimension key uniqueness
SELECT 'dim_date' AS dim, COUNT(*) AS rows, COUNT(DISTINCT date_key) AS distinct_keys FROM workspace.gold.dim_date UNION ALL
SELECT 'dim_customer', COUNT(*), COUNT(DISTINCT customer_id) FROM workspace.gold.dim_customer UNION ALL
SELECT 'dim_product', COUNT(*), COUNT(DISTINCT product_card_id) FROM workspace.gold.dim_product UNION ALL
SELECT 'dim_category', COUNT(*), COUNT(DISTINCT category_id) FROM workspace.gold.dim_category UNION ALL
SELECT 'dim_department', COUNT(*), COUNT(DISTINCT department_id) FROM workspace.gold.dim_department UNION ALL
SELECT 'dim_geo', COUNT(*), COUNT(DISTINCT geo_key) FROM workspace.gold.dim_geo UNION ALL
SELECT 'dim_channel', COUNT(*), COUNT(DISTINCT channel_key) FROM workspace.gold.dim_channel UNION ALL
SELECT 'dim_discount_band', COUNT(*), COUNT(DISTINCT discount_band_key) FROM workspace.gold.dim_discount_band;

-- 3) Fact grain uniqueness
SELECT 'fact_sales' AS fact, COUNT(*) AS rows, COUNT(DISTINCT order_item_id) AS distinct_order_item_id
FROM workspace.gold.fact_sales
UNION ALL
SELECT 'fact_fulfilment', COUNT(*), COUNT(DISTINCT order_item_id)
FROM workspace.gold.fact_fulfilment;

-- 4) Fact key null checks
SELECT
  'fact_sales' AS fact,
  SUM(CASE WHEN order_item_id IS NULL THEN 1 ELSE 0 END) AS null_order_item_id,
  SUM(CASE WHEN order_id      IS NULL THEN 1 ELSE 0 END) AS null_order_id,
  SUM(CASE WHEN customer_id   IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
  SUM(CASE WHEN product_card_id IS NULL THEN 1 ELSE 0 END) AS null_product_card_id,
  SUM(CASE WHEN order_date_key IS NULL THEN 1 ELSE 0 END) AS null_order_date_key
FROM workspace.gold.fact_sales;

SELECT
  'fact_fulfilment' AS fact,
  SUM(CASE WHEN order_item_id IS NULL THEN 1 ELSE 0 END) AS null_order_item_id,
  SUM(CASE WHEN order_id      IS NULL THEN 1 ELSE 0 END) AS null_order_id,
  SUM(CASE WHEN customer_id   IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
  SUM(CASE WHEN product_card_id IS NULL THEN 1 ELSE 0 END) AS null_product_card_id,
  SUM(CASE WHEN order_date_key IS NULL THEN 1 ELSE 0 END) AS null_order_date_key,
  SUM(CASE WHEN ship_date_key  IS NULL THEN 1 ELSE 0 END) AS null_ship_date_key
FROM workspace.gold.fact_fulfilment;

-- 5) FK coverage (fact_sales -> dims)
SELECT
  SUM(CASE WHEN d.date_key IS NULL THEN 1 ELSE 0 END) AS missing_order_date_dim,
  SUM(CASE WHEN c.customer_id IS NULL THEN 1 ELSE 0 END) AS missing_customer_dim,
  SUM(CASE WHEN p.product_card_id IS NULL THEN 1 ELSE 0 END) AS missing_product_dim,
  SUM(CASE WHEN g.geo_key IS NULL THEN 1 ELSE 0 END) AS missing_geo_dim,
  SUM(CASE WHEN ch.channel_key IS NULL THEN 1 ELSE 0 END) AS missing_channel_dim,
  SUM(CASE WHEN b.discount_band_key IS NULL THEN 1 ELSE 0 END) AS missing_discount_band_dim,
  SUM(CASE WHEN cat.category_id IS NULL THEN 1 ELSE 0 END) AS missing_category_dim,
  SUM(CASE WHEN dep.department_id IS NULL THEN 1 ELSE 0 END) AS missing_department_dim,
  COUNT(*) AS fact_rows
FROM workspace.gold.fact_sales f
LEFT JOIN workspace.gold.dim_date d           ON f.order_date_key = d.date_key
LEFT JOIN workspace.gold.dim_customer c       ON f.customer_id = c.customer_id
LEFT JOIN workspace.gold.dim_product p        ON f.product_card_id = p.product_card_id
LEFT JOIN workspace.gold.dim_geo g            ON f.geo_key = g.geo_key
LEFT JOIN workspace.gold.dim_channel ch       ON f.channel_key = ch.channel_key
LEFT JOIN workspace.gold.dim_discount_band b  ON f.discount_band_key = b.discount_band_key
LEFT JOIN workspace.gold.dim_category cat     ON f.category_id = cat.category_id
LEFT JOIN workspace.gold.dim_department dep   ON f.department_id = dep.department_id;

-- 6) FK coverage (fact_fulfilment -> dims)
SELECT
  SUM(CASE WHEN d1.date_key IS NULL THEN 1 ELSE 0 END) AS missing_order_date_dim,
  SUM(CASE WHEN d2.date_key IS NULL THEN 1 ELSE 0 END) AS missing_ship_date_dim,
  SUM(CASE WHEN c.customer_id IS NULL THEN 1 ELSE 0 END) AS missing_customer_dim,
  SUM(CASE WHEN p.product_card_id IS NULL THEN 1 ELSE 0 END) AS missing_product_dim,
  SUM(CASE WHEN g.geo_key IS NULL THEN 1 ELSE 0 END) AS missing_geo_dim,
  SUM(CASE WHEN ch.channel_key IS NULL THEN 1 ELSE 0 END) AS missing_channel_dim,
  SUM(CASE WHEN cat.category_id IS NULL THEN 1 ELSE 0 END) AS missing_category_dim,
  SUM(CASE WHEN dep.department_id IS NULL THEN 1 ELSE 0 END) AS missing_department_dim,
  COUNT(*) AS fact_rows
FROM workspace.gold.fact_fulfilment f
LEFT JOIN workspace.gold.dim_date d1      ON f.order_date_key = d1.date_key
LEFT JOIN workspace.gold.dim_date d2      ON f.ship_date_key  = d2.date_key
LEFT JOIN workspace.gold.dim_customer c   ON f.customer_id = c.customer_id
LEFT JOIN workspace.gold.dim_product p    ON f.product_card_id = p.product_card_id
LEFT JOIN workspace.gold.dim_geo g        ON f.geo_key = g.geo_key
LEFT JOIN workspace.gold.dim_channel ch   ON f.channel_key = ch.channel_key
LEFT JOIN workspace.gold.dim_category cat ON f.category_id = cat.category_id
LEFT JOIN workspace.gold.dim_department dep ON f.department_id = dep.department_id;

-- 7) Sanity checks (optional)
SELECT
  MIN(discount_rate) AS min_discount_rate,
  MAX(discount_rate) AS max_discount_rate,
  MIN(net_sales)     AS min_net_sales,
  MIN(gross_sales)   AS min_gross_sales,
  MIN(profit)        AS min_profit
FROM workspace.gold.fact_sales;

SELECT
  MIN(shipping_days_variance) AS min_variance,
  MAX(shipping_days_variance) AS max_variance,
  SUM(CASE WHEN shipping_days_variance > 0 THEN 1 ELSE 0 END) AS late_lines,
  COUNT(*) AS total_lines
FROM workspace.gold.fact_fulfilment;
