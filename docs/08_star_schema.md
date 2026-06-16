# Gold Star Schema (Dataco Supply Chain)

> **Scope:** the Gold star schema + the Power BI model layer built on it. The v1 core schema is unchanged in v2; v2 adds a measure layer and parameter/security tables (marked **(v2)** below), plus a synthesized `dim_contract_terms` staging dim. Column-level detail: [`03_data_dictionary_notes.md`](03_data_dictionary_notes.md).

## Source

- Silver input: `workspace.silver.dataco_supplychain_clean_current`
- Gold schema: `workspace.gold` (PySpark core build `01_gold_build.py`; v2 enrichment `02_gold_schema_remediation.py`)
- Durable serving layer: `data/databricks_gold_export/` (CSV)

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

### Model-layer & v2 additions (not Gold CSVs unless noted)

- `DIM_MARKET` — **security dimension**: distinct list of markets, 1 row per market. Required so Market slicers bind a clean key for RLS propagation. (Model table, derived from the market list.)
- `SEC_USER_MARKET` — **RLS mapping**: `UserEmail` → `MARKET`. Entered/maintained in the model; drives the `MarketManager` role. See [`10_rls.md`](10_rls.md).
- `dim_contract_terms` — **(v2 · synthesized)** Gold CSV: rebate tiers & SLA terms by `customer_segment`. Staged for a v3 segment-aware rebate; not yet joined in the shipped model. See [`03`](03_data_dictionary_notes.md) §3.11.
- `Parameter_Dimensions`, `Scenario_FreightSurcharge`, `Scenario_MOQ`, `Scenario_Rebate` — **(v2)** calculated parameter tables powering the field-parameter axis swap and the three What-If sliders. See [`02`](02_kpi_glossary.md) §G.

## Join Map (Power BI)

- `fact_sales.order_date_key` → `dim_date.date_key` — **active** (primary date)
- `fact_fulfilment.order_date_key` → `dim_date.date_key` — **active**
- `fact_fulfilment.ship_date_key` → `dim_date.date_key` — **inactive**, activated per-measure via `USERELATIONSHIP()` (ship-date role-play)
- `fact_sales.customer_id` → `dim_customer.customer_id`
- `fact_sales.product_card_id` → `dim_product.product_card_id`
- `fact_sales.category_id` → `dim_category.category_id`
- `fact_sales.department_id` → `dim_department.department_id`
- `fact_sales.geo_key` → `dim_geo.geo_key`
- `fact_sales.channel_key` → `dim_channel.channel_key`
- `fact_sales.discount_band_key` → `dim_discount_band.discount_band_key` *(sales-only)*
- **Both facts join the shared dims** (date/customer/product/category/department/geo/channel) — so one category/market/mode slicer filters commercial **and** fulfilment measures consistently. Only `dim_discount_band` is `fact_sales`-exclusive.

**RLS propagation chain (v1, verified in v2):**

- `DIM_CHANNEL.MARKET` → `DIM_MARKET.MARKET` — single direction
- `SEC_USER_MARKET.MARKET` ↔ `DIM_MARKET.MARKET` — **both directions** (propagates the `MarketManager` filter into the model). Market slicers must bind `DIM_MARKET[MARKET]`, never `DIM_CHANNEL[MARKET]`.

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
- Fulfilment variance: `shipping_days_variance` (= `days_for_shipping_real − days_for_shipment_scheduled`, precomputed in Gold)
- **Late indicator (dashboard headline):** `late_delivery_risk` (binary flag, 54.8% portfolio). `is_late_by_days` is a secondary severity signal (57.3%). See [`09`](09_gold_data_quality_report.md).

## v2 Commercial Measure Layer (built on the same grain)

The v2 measures are pure DAX on top of this star schema — no schema change was required to add them:

- **Cost-to-Serve (folder K):** `Handling Cost (ABC)`, `Freight Cost (Est)`, `MOQ Penalty Surcharge`, `Total Cost-to-Serve`, `CTS % of Net Sales`, `Net Commercial Margin`(`%`).
- **Risk & Trade Spend (folder L):** `Revenue at Risk (Late SLA)` (bridges the two facts via `order_id` set membership — no direct fact-to-fact FK), `Estimated SLA Penalty`, `Retailer Rebate Accrual`, `True Net Profit (Post-Rebate)`.
- **Scenario Planning (folder L):** harvest measures over the three `Scenario_*` tables; `Parameter_Dimensions` supplies the swappable axis.

Full definitions and exact DAX: [`02_kpi_glossary.md`](02_kpi_glossary.md) §E–G.
