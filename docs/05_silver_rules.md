# Silver Rules

## Inputs

- Source: `bronze.dataco_supplychain_raw_audited` (audited Bronze table)
- Output: `silver.dataco_supplychain_clean`
- Lineage preserved: `_ingest_ts`, `_batch_id`

## Type standardisation (what was cast)

- IDs cast to BIGINT: `order_item_id`, `order_id`, `customer_id`, `product_card_id`, `category_id`, `department_id`
- Monetary fields cast to DOUBLE: `gross_sales`, `net_sales`, `discount_amount`, `discount_rate`, `profit`, `unit_price`, `catalog_price`
- Quantity cast to INT: `quantity`
- Zipcodes cast to STRING: `order_zipcode`, `customer_zipcode` (preserves leading zeros)
- Latitude/Longitude cast to DOUBLE

## Timestamp parsing (how it was parsed)

- Raw timestamp strings preserved: `order_ts_raw`, `ship_ts_raw`
- Parsed timestamps created: `order_ts`, `ship_ts`
- Supported formats via COALESCE:
  - `M/d/yyyy H:mm`
  - `MM/dd/yyyy HH:mm`
  - `M/d/yyyy H:mm:ss`
  - `MM/dd/yyyy HH:mm:ss`
- Derived date columns:
  - `order_date = to_date(order_ts)`
  - `ship_date  = to_date(ship_ts)`

## Derived fields created

- `is_late_by_days = CASE WHEN days_for_shipping_real > days_for_shipment_scheduled THEN 1 ELSE 0 END`

## PII removed (dropped/excluded)

Excluded from Silver/Gold:

- `customer_email`
- `customer_password`
- `customer_street`
- `customer_fname`, `customer_lname`
