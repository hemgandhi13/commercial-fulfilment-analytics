-- A) v1 vs v2 row counts 
SELECT
  (SELECT COUNT(*) FROM workspace.silver.dataco_supplychain_clean)    AS silver_v1_rows,
  (SELECT COUNT(*) FROM workspace.silver.dataco_supplychain_clean_v2) AS silver_v2_rows;

-- B) How many rows were actually corrected by standardisation 
SELECT
  SUM(CASE WHEN order_region <> order_region_std THEN 1 ELSE 0 END) AS region_corrected_rows,
  SUM(CASE WHEN market      <> market_std      THEN 1 ELSE 0 END) AS market_corrected_rows,
  SUM(CASE WHEN shipping_mode <> shipping_mode_std THEN 1 ELSE 0 END) AS shipmode_corrected_rows,
  COUNT(*) AS total_rows
FROM workspace.silver.dataco_supplychain_clean_v2;

-- C) Encoding corruption counts 
SELECT
  SUM(CASE WHEN order_country_std LIKE '%�%' THEN 1 ELSE 0 END) AS bad_country_rows,
  SUM(CASE WHEN order_city_std    LIKE '%�%' THEN 1 ELSE 0 END) AS bad_city_rows,
  COUNT(*) AS total_rows
FROM workspace.silver.dataco_supplychain_clean_v2;

-- D) Zipcode nulls 
SELECT
  SUM(CASE WHEN order_zipcode_std IS NULL THEN 1 ELSE 0 END) AS null_order_zip,
  COUNT(*) AS total_rows
FROM workspace.silver.dataco_supplychain_clean_v2;
