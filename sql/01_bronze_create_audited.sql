  CREATE OR REPLACE TABLE bronze.dataco_supplychain_raw_audited AS
SELECT
  *,
  current_timestamp() AS _ingest_ts,
  'day1_initial' AS _batch_id
FROM bronze.dataco_supplychain_raw;