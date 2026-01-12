# Gold Star Schema (Dataco Supply Chain)

## Source

- Silver input: `workspace.silver.dataco_supplychain_clean_current`
- Gold schema: `workspace.gold`

## Declared Grain

- **Facts are at order-line grain**: **1 row per `order_item_id`**.

## Table Inventory

### Dimensions

- `gold.dim_date`

  - Key: `date_key` (INT `yyyyMMdd`)
  - Role-playing: used as both Order Date and Ship Date

- `gold.dim_customer`

  - Key: `customer_id`
  - Attributes: segment + customer geo descriptors + `customer_*_key` normalised keys

- `gold.dim_product`

  - Key: `product_card_id`
  - Attributes: product + category/department identifiers

- `gold.dim_category`

  - Key: `category_id`
  - Attributes: `category_name` (sourced from Bronze)

- `gold.dim_department`

  - Key: `department_id`
  - Attributes: `department_name` (sourced from Bronze)

- `gold.dim_geo`

  - Key: `geo_key` (BIGINT)
  - Grain: **country/state/city**
  - Design: `geo_key = xxhash64(order_country_key, order_state_key, order_city_key)`
  - Rationale: Zipcode is frequently NULL; therefore zipcode is not part of geo grain.

- `gold.dim_channel`

  - Key: `channel_key` (BIGINT)
  - Grain: **market/order_region/shipping_mode**
  - Design: `channel_key = xxhash64(market_key, order_region_key, shipping_mode_key)`

- `gold.dim_discount_band`
  - Key: `discount_band_key`
  - Bands: 0%, >0–5%, >5–10%, >10–15%, >15–20%, >20–25%

### Facts

- `gold.fact_sales`

  - Grain: `order_item_id`
  - Measures: `gross_sales`, `net_sales`, `discount_amount`, `discount_rate`, `profit`, `quantity`, `unit_price`
  - Dim keys: `order_date_key`, `geo_key`, `channel_key`, `discount_band_key`

- `gold.fact_fulfilment`
  - Grain: `order_item_id`
  - Measures/signals: shipping actual vs scheduled, variance, late risk, `is_late_by_days`
  - Dim keys: `order_date_key`, `ship_date_key`, `geo_key`, `channel_key`

## Join Map (Power BI)

- `fact_sales.order_date_key` → `dim_date.date_key`
- `fact_fulfilment.order_date_key` → `dim_date.date_key`
- `fact_fulfilment.ship_date_key` → `dim_date.date_key`
- `fact_sales.customer_id` → `dim_customer.customer_id`
- `fact_sales.product_card_id` → `dim_product.product_card_id`
- `fact_sales.category_id` → `dim_category.category_id`
- `fact_sales.department_id` → `dim_department.department_id`
- `fact_sales.geo_key` → `dim_geo.geo_key`
- `fact_sales.channel_key` → `dim_channel.channel_key`
- (same join strategy for fulfilment fact)

## Notes on Hash Keys

- `xxhash64(...)` is used to create compact surrogate keys for multi-column natural keys.
- `coalesce(...,'')` is applied to ensure deterministic keys even when some components are NULL.
- This avoids the SQL `NULL = NULL` mismatch issue during joining.

## KPI Mapping (core)

- Revenue: `gross_sales`
- Net sales: `net_sales`
- Discount value: `discount_amount`
- Discount rate: `discount_rate`
- Profit: `profit`
- Volume: `quantity`
- Unit price: `unit_price`
- Fulfilment variance: `days_for_shipping_real - days_for_shipment_scheduled`
- Late indicator: `is_late_by_days`
