# 03 — Data Dictionary Notes (Gold Layer, Databricks)

This document defines the **Gold star schema contract** produced in **Databricks** for the Dataco Supply Chain dataset.
It is intentionally **Databricks-first**: table grain, keys, and column meanings as implemented in the Gold layer.

**Gold schema location (Databricks):** `workspace.gold`  
**Durable serving layer:** `data/databricks_gold_export/` (the version-controlled CSV export Power BI reads)  
**Declared grain:** Facts are at **order-line grain** → **1 row per `order_item_id`**.

> ### Two-stage Gold build (v1 core + v2 enrichment)
>
> | Stage | Script | Engine | Produces |
> | :---- | :----- | :----- | :------- |
> | **1. Core star schema** (v1) | `data-pipeline/01_gold_build.py` | PySpark | `fact_sales`, `fact_fulfilment` + 8 dims, with `xxhash64` surrogate keys cast to string and post-write schema assertions |
> | **2. Commercial enrichment** (v2) | `data-pipeline/02_gold_schema_remediation.py` | pandas (on the CSV export) | Appends CTS/ABC, logistics-financial, DIFOT-date, SLA-contract, rebate, and waterfall columns; creates **`dim_contract_terms`** |
>
> **⚠ Provenance — read before trusting v2 columns.** DataCo ships commercial and fulfilment facts but **no** cost-to-serve, freight, weight/volume, SLA-contract, rebate-tier, or promotional attributes. Stage 2 supplies these as a **deterministic (seed-42), benchmark-modelled** enrichment using FMCG/retail industry rates. Stage-2 columns are flagged **`(v2 · synthesized)`** below. They are honest stand-ins so the commercial *methods* (ABC costing, DIFOT financialization, tiered rebates, scenario planning) can be demonstrated; replace with actuals when available. Stage-2 also self-reports a PASS/MOCKED diagnostic matrix on every run (mirrored in [`09`](09_gold_data_quality_report.md) §7).
>
> **What the v2 *model* actually consumes:** the DAX cost/penalty/rebate measures use **hard-coded rate assumptions** (see [`02_kpi_glossary.md`](02_kpi_glossary.md) §E–F), **not** most of these columns. The finer-grained Stage-2 columns (`base_freight_cost`, `warehouse_handling_fee`, `sla_penalty_pct_per_day`, `dim_contract_terms`) are **staged for a v3 "contract-true" rewrite** and are not yet wired into measures.

---

## 1) Modelling contract

### 1.1 Naming

- `fact_*` tables contain additive measures and foreign keys to dimensions.
- `dim_*` tables contain descriptive attributes used for slicing/filtering.

### 1.2 Keys

- Dimension primary keys:
  - `dim_date.date_key` (INT, `yyyyMMdd`)
  - `dim_customer.customer_id`
  - `dim_product.product_card_id`
  - `dim_category.category_id`
  - `dim_department.department_id`
  - `dim_geo.geo_key` (BIGINT)
  - `dim_channel.channel_key` (BIGINT)
  - `dim_discount_band.discount_band_key`
- Fact primary key: `order_item_id` (unique in each fact).
- Join rule: facts join to dimensions on the corresponding key columns.

### 1.3 Date role-playing

`dim_date` is used for multiple business dates:

- **Order Date:** `fact_sales.order_date_key` and `fact_fulfilment.order_date_key`
- **Ship Date:** `fact_fulfilment.ship_date_key`

### 1.4 Hash key dimensions (design decision)

Two dimensions use compact surrogate keys derived from multiple natural-key columns:

- `dim_geo.geo_key = xxhash64(order_country_key, order_state_key, order_city_key)`
  - **Zipcode is excluded** from geo grain due to frequent NULLs.
- `dim_channel.channel_key = xxhash64(market_key, order_region_key, shipping_mode_key)`

These are deterministic with `coalesce(...,'')` to prevent null-induced drift.

---

## 2) Table inventory (Gold)

### Dimensions

- `gold.dim_date`
- `gold.dim_customer`
- `gold.dim_product`
- `gold.dim_category`
- `gold.dim_department`
- `gold.dim_geo`
- `gold.dim_channel`
- `gold.dim_discount_band`
- `gold.dim_contract_terms` — **(v2 · synthesized)** rebate-tier & SLA contract terms by customer segment (§3.11)

### Facts

- `gold.fact_sales`
- `gold.fact_fulfilment`
- `gold.fact_order_item` — **export-only convenience fact**: a wide join of sales + fulfilment at the same `order_item_id` grain, produced for the Snowflake serving layer (§3.12). Carries the v1 columns only; the v2 enrichment was applied to `fact_sales`/`fact_fulfilment`, not this table.

> **Model-only tables (not Gold CSVs):** `DIM_MARKET` (distinct markets, for RLS) and `SEC_USER_MARKET` (user→market map) live in the Power BI semantic model, not the Gold layer — see [`08_star_schema.md`](08_star_schema.md) and [`10_rls.md`](10_rls.md).

---

## 3) Column dictionary

> Types are expressed as **logical types**. In Spark, numeric fields may be `INT`, `BIGINT`, `DOUBLE`, `DECIMAL`, etc.
> Treat keys as integers (no scientific notation), and preserve ZIP/postcodes as **text** downstream.

---

### 3.1 `gold.fact_sales` — Commercial

**Grain:** 1 row per `order_item_id`  
**Primary key:** `order_item_id`  
**Foreign keys:** `order_date_key`, `customer_id`, `product_card_id`, `category_id`, `department_id`, `geo_key`, `channel_key`, `discount_band_key`

| Column            | Type           | Definition / Notes                                                  |
| ----------------- | -------------- | ------------------------------------------------------------------- |
| order_item_id     | integer        | Order line identifier (PK; unique).                                 |
| order_id          | integer        | Order header identifier (degenerate dimension).                     |
| customer_id       | integer        | FK → `dim_customer`.                                                |
| product_card_id   | integer        | FK → `dim_product`.                                                 |
| category_id       | integer        | FK → `dim_category`.                                                |
| department_id     | integer        | FK → `dim_department`.                                              |
| order_date_key    | integer        | FK → `dim_date` (`yyyyMMdd`).                                       |
| geo_key           | bigint         | FK → `dim_geo` (hashed).                                            |
| channel_key       | bigint         | FK → `dim_channel` (hashed).                                        |
| discount_band_key | integer        | FK → `dim_discount_band`.                                           |
| gross_sales       | numeric        | Sales value before discount (baseline commercial volume).           |
| net_sales         | numeric        | Revenue after discounts (used as “Net Sales”).                      |
| discount_amount   | numeric        | Discount value applied to the line.                                 |
| discount_rate     | numeric        | Discount rate (0–0.25 observed in Gold validation).                 |
| profit            | numeric        | Profit per line; negative values allowed (loss-making lines exist). |
| quantity          | integer        | Units sold.                                                         |
| unit_price        | numeric        | Selling unit price (line-level).                                    |
| order_status      | string         | Order status label.                                                 |
| \_ingest_ts       | timestamp      | Lineage timestamp (tech).                                           |
| \_batch_id        | string/integer | Lineage batch identifier (tech).                                    |

**Derived/engineering notes**

- `discount_band_key` is assigned based on `discount_rate` into bands:
  - 0%, >0–5%, >5–10%, >10–15%, >15–20%, >20–25%.

**v2 enrichment columns** — appended by `02_gold_schema_remediation.py`. All **(v2 · synthesized)** except `order_date`; same `order_item_id` grain (cost columns joined from `fact_fulfilment`).

| Column              | Type    | Definition / Notes                                                                 |
| ------------------- | ------- | ---------------------------------------------------------------------------------- |
| order_date          | date    | Calendar order date reconstructed from `order_date_key` (DAX convenience; not synthesized). |
| is_promotional      | integer (0/1) | Order flagged promotional. ~25% of **orders** (seeded on `order_id`, so all lines of an order agree). |
| base_freight_cost   | numeric | Per-unit base freight by mode (Same Day $8.50 / First $5 / Second $3 / Standard $1.75). |
| fuel_surcharge      | numeric | 8% of `base_freight_cost` (industry fuel levy).                                    |
| warehouse_handling_fee | numeric | Per-line handling by `delivery_type` ($4.00 / $2.50 / $1.50).                    |
| delivery_type       | string  | Same-Day Express / Major DC Pallet Drop / Regional Fragmented Delivery (from mode). |
| gross_revenue       | numeric | Alias of `gross_sales` (explicit anchor name for the Deneb waterfall spec).         |
| base_fuel_cost      | numeric | = `fuel_surcharge`, named for What-If slider isolation.                             |
| cost_to_serve_amount | numeric | `base_freight_cost + fuel_surcharge + warehouse_handling_fee` (per line).          |
| net_margin          | numeric | `profit − cost_to_serve_amount` (row-level CTS margin; negatives expected).         |

> These columns are **column-level inputs** for a future contract-true CTS rewrite. The shipped v2 DAX computes CTS from rate assumptions instead (see [`02`](02_kpi_glossary.md) §E) — so most of these are not yet read by any measure.

---

### 3.2 `gold.fact_fulfilment` — Operations / Delivery

**Grain:** 1 row per `order_item_id`  
**Primary key:** `order_item_id`  
**Foreign keys:** `order_date_key`, `ship_date_key`, `customer_id`, `product_card_id`, `category_id`, `department_id`, `geo_key`, `channel_key`

| Column                      | Type           | Definition / Notes                                            |
| --------------------------- | -------------- | ------------------------------------------------------------- |
| order_item_id               | integer        | Order line identifier (PK; unique).                           |
| order_id                    | integer        | Order header identifier.                                      |
| customer_id                 | integer        | FK → `dim_customer`.                                          |
| product_card_id             | integer        | FK → `dim_product`.                                           |
| category_id                 | integer        | FK → `dim_category`.                                          |
| department_id               | integer        | FK → `dim_department`.                                        |
| order_date_key              | integer        | FK → `dim_date` (`yyyyMMdd`).                                 |
| ship_date_key               | integer        | FK → `dim_date` (`yyyyMMdd`) for ship date role.              |
| geo_key                     | bigint         | FK → `dim_geo` (hashed).                                      |
| channel_key                 | bigint         | FK → `dim_channel` (hashed).                                  |
| days_for_shipping_real      | integer        | Actual shipping days.                                         |
| days_for_shipment_scheduled | integer        | Scheduled shipping days.                                      |
| shipping_days_variance      | integer        | Actual − scheduled (range −2 to 4 observed).                  |
| late_delivery_risk          | integer (0/1)  | Late flag used for Late Delivery Rate.                        |
| is_late_by_days             | integer        | Days late (if late).                                          |
| delivery_status             | string         | Delivery status label.                                        |
| shipping_mode               | string         | Shipping mode label (e.g., Standard, First Class).            |
| order_status                | string         | Order status label.                                           |
| order_zipcode               | string         | Zip/postcode from order; not used for geo grain due to nulls. |
| \_ingest_ts                 | timestamp      | Lineage timestamp (tech).                                     |
| \_batch_id                  | string/integer | Lineage batch identifier (tech).                              |

**v2 enrichment columns** — appended by `02_gold_schema_remediation.py`. All **(v2 · synthesized)** except the date reconstructions; same `order_item_id` grain.

| Column                  | Type    | Definition / Notes                                                            |
| ----------------------- | ------- | ----------------------------------------------------------------------------- |
| delivery_type           | string  | Same-Day Express / Major DC Pallet Drop / Regional Fragmented Delivery (from `shipping_mode`). |
| base_freight_cost       | numeric | Per-unit base freight by mode (Same Day $8.50 / First $5 / Second $3 / Standard $1.75). |
| fuel_surcharge          | numeric | 8% of `base_freight_cost`.                                                    |
| warehouse_handling_fee  | numeric | Per-line handling by `delivery_type` ($4.00 / $2.50 / $1.50).                  |
| sla_target_days         | integer | Contractual delivery SLA by mode: Same Day 1 / First 3 / Second 5 / Standard 7. |
| sla_penalty_pct_per_day | numeric | Flat **0.02** (2% of invoice/day late after 24h grace). v3 input for day-accurate penalties. |
| order_date              | date    | Reconstructed from `order_date_key` (not synthesized).                        |
| ship_date               | date    | Reconstructed from `ship_date_key` (not synthesized).                         |
| expected_delivery_date  | date    | `ship_date + sla_target_days` (derived).                                      |
| actual_delivery_date    | date    | `ship_date + days_for_shipping_real`; **NULL** for `Shipping canceled` (open pipeline). |
| pipeline_status         | string  | In Transit - Late / In Transit - On Time / Backordered-Canceled / Unknown (from `delivery_status`). |

> Stage-2 integrity gates (all PASS): chronological `order_date ≤ expected_delivery_date`, ship-date orphan check, and `total_logistics_cost ≤ gross_sales` on every row. The v2 DAX still measures lateness from the binary `late_delivery_risk` flag — these dated columns are v3 enablement.

---

### 3.3 `gold.dim_date` — Calendar

**Primary key:** `date_key` (INT `yyyyMMdd`)

| Column       | Type    | Definition                         |
| ------------ | ------- | ---------------------------------- |
| date_key     | integer | Surrogate key (yyyyMMdd).          |
| date         | date    | Calendar date.                     |
| year         | integer | Year.                              |
| quarter      | integer | Quarter (1–4).                     |
| month        | integer | Month number (1–12).               |
| year_month   | string  | YYYY-MM label (for reporting).     |
| week_of_year | integer | ISO-like week number (as derived). |
| day_name     | string  | Day name.                          |
| day_of_week  | integer | Day-of-week number.                |

---

### 3.4 `gold.dim_customer` — Customer descriptors (non-PII)

**Primary key:** `customer_id`

| Column               | Type    | Definition                                          |
| -------------------- | ------- | --------------------------------------------------- |
| customer_id          | integer | Customer surrogate key.                             |
| customer_segment     | string  | Segment (Consumer/Corporate/Home Office).           |
| customer_country     | string  | Country label.                                      |
| customer_state       | string  | State label.                                        |
| customer_city        | string  | City label.                                         |
| customer_zipcode     | string  | Zip/postcode (stored as text).                      |
| latitude             | numeric | Customer latitude (if present).                     |
| longitude            | numeric | Customer longitude (if present).                    |
| customer_country_key | string  | Normalised key string used upstream (standardised). |
| customer_state_key   | string  | Normalised key string used upstream (standardised). |
| customer_city_key    | string  | Normalised key string used upstream (standardised). |
| customer_zipcode_key | string  | Normalised key string used upstream (standardised). |

**Governance note:** PII fields (email, password, street, first/last name) are excluded from analytics layers by design.

---

### 3.5 `gold.dim_product` — Product descriptors

**Primary key:** `product_card_id`

| Column              | Type    | Definition                                             |
| ------------------- | ------- | ------------------------------------------------------ |
| product_card_id     | integer | Product surrogate key.                                 |
| product_name        | string  | Product name.                                          |
| product_category_id | integer | Source category identifier (if present).               |
| category_id         | integer | FK to `dim_category` (denormalised for convenience).   |
| department_id       | integer | FK to `dim_department` (denormalised for convenience). |
| catalog_price       | numeric | Catalogue/list price.                                  |
| product_description | string  | Product description text.                              |
| product_status      | string  | Product status label.                                  |

**v2 enrichment columns** — appended by `02_gold_schema_remediation.py`, **(v2 · synthesized)** to FMCG/sporting-goods volumetric benchmarks.

| Column         | Type    | Definition / Notes                                            |
| -------------- | ------- | ------------------------------------------------------------ |
| unit_weight_kg | numeric | Per-unit weight (0.2–20 kg, weighted toward 0.5–2 kg).        |
| unit_volume_m3 | numeric | Per-unit volume (≈ weight × 0.0015 ± 30%).                    |
| storage_type   | string  | `Pallet` if ≥ 5 kg else `Carton` (drives the handling tier).  |

---

### 3.6 `gold.dim_category`

**Primary key:** `category_id`

| Column        | Type    | Definition      |
| ------------- | ------- | --------------- |
| category_id   | integer | Category key.   |
| category_name | string  | Category label. |

---

### 3.7 `gold.dim_department`

**Primary key:** `department_id`

| Column          | Type    | Definition        |
| --------------- | ------- | ----------------- |
| department_id   | integer | Department key.   |
| department_name | string  | Department label. |

---

### 3.8 `gold.dim_geo` — Order geography (hashed key)

**Primary key:** `geo_key`

| Column  | Type   | Definition                           |
| ------- | ------ | ------------------------------------ |
| geo_key | bigint | Hashed key for (country/state/city). |
| country | string | Order country.                       |
| state   | string | Order state.                         |
| city    | string | Order city.                          |

---

### 3.9 `gold.dim_channel` — Market / region / shipping mode (hashed key)

**Primary key:** `channel_key`

| Column            | Type   | Definition                                          |
| ----------------- | ------ | --------------------------------------------------- |
| channel_key       | bigint | Hashed key for (market/order_region/shipping_mode). |
| market            | string | Market label.                                       |
| order_region      | string | Order region label.                                 |
| shipping_mode     | string | Shipping mode label.                                |
| market_key        | string | Normalised key string (upstream).                   |
| order_region_key  | string | Normalised key string (upstream).                   |
| shipping_mode_key | string | Normalised key string (upstream).                   |

---

### 3.10 `gold.dim_discount_band` — Discount buckets

**Primary key:** `discount_band_key`

| Column              | Type    | Definition                                           |
| ------------------- | ------- | ---------------------------------------------------- |
| discount_band_key   | integer | Band key.                                            |
| discount_band_label | string  | Human-friendly band label.                           |
| rate_min            | numeric | Lower bound (inclusive/exclusive as per build rule). |
| rate_max            | numeric | Upper bound.                                         |

---

### 3.11 `gold.dim_contract_terms` — Rebate & SLA contract terms **(v2 · synthesized)**

**New table in v2**, written by `02_gold_schema_remediation.py` (9 rows). Modelled on an FMCG tiered retrospective-rebate framework.
**Grain:** 1 row per `customer_segment` × `tier_label`.
**Intended join:** `dim_customer.customer_segment = dim_contract_terms.customer_segment`.

| Column                       | Type    | Definition                                                     |
| ---------------------------- | ------- | ------------------------------------------------------------- |
| customer_segment             | string  | Consumer / Corporate / Home Office.                           |
| tier_label                   | string  | Bronze / Silver / Gold (by annual spend).                    |
| annual_spend_min_usd         | numeric | Tier lower bound (USD).                                       |
| annual_spend_max_usd         | numeric | Tier upper bound (USD).                                       |
| rebate_pct                   | numeric | Rebate rate for the tier (0.01–0.05).                         |
| payment_terms_days           | integer | Net payment terms (30 / 45 / 60).                            |
| sla_service_level_target_pct | numeric | Target service level (0.90–0.98).                            |
| sla_penalty_pct_per_day      | numeric | Flat 0.02 (consistent with `fact_fulfilment`).               |
| grace_period_hours           | integer | 24.                                                          |

> **Not yet consumed by the v2 model.** The shipped `Retailer Rebate Accrual` measure uses a simpler volume `SWITCH` (5% > $5M, 3% > $1M, else 1%). This table stages a segment-aware rebate for v3.

---

### 3.12 `gold.fact_order_item` — Wide convenience fact (export/Snowflake)

**Grain:** 1 row per `order_item_id` (180,519). A denormalised join of `fact_sales` + `fact_fulfilment` produced for the Snowflake serving layer and shipped in the CSV export. Columns are the **v1 union** of both facts (sales measures + fulfilment signals + both date keys + `discount_band_key`); it does **not** carry the Stage-2 v2 enrichment columns. Power BI's model uses the two narrow facts, not this table — it exists for single-table SQL/BI consumers.

---

## 4) Gold data quality expectations (contract)

Gold build is considered valid when all conditions below hold:

### 4.1 Row counts (snapshot reference)

- `dim_date`: 1,133
- `dim_customer`: 20,652
- `dim_product`: 118
- `dim_category`: 51
- `dim_department`: 11
- `dim_geo`: 3,772
- `dim_channel`: 92
- `dim_discount_band`: 6
- `dim_contract_terms`: 9  *(v2)*
- `fact_sales`: 180,519
- `fact_fulfilment`: 180,519
- `fact_order_item`: 180,519  *(export-only wide fact)*

### 4.2 Uniqueness

- Each dimension key is unique (rows = distinct PK).
- Each fact has unique `order_item_id` (rows = distinct order_item_id).

### 4.3 FK coverage

- All fact-to-dimension joins must have **0 missing keys**.

### 4.4 Metric sanity (observed ranges)

- `discount_rate`: 0 to 0.25
- `profit`: negative values allowed (loss lines exist)
- `shipping_days_variance`: -2 to 4

---

## 5) Change control (do-not-break rules)

If any of these change, downstream semantic layers may break and must be versioned:

1. Table names (`gold.fact_sales`, `gold.dim_date`, etc.)
2. Primary keys and FK columns
3. Grain (facts must stay at order-line)
4. Core KPI driver columns: `gross_sales`, `net_sales`, `profit`, `discount_amount`, `discount_rate`, shipping-day fields, `late_delivery_risk` (the binary lateness flag the dashboard's Late Delivery Rate keys off)
5. **(v2)** Stage-2 enrichment columns consumed by DAX or report visuals — currently `gross_revenue` (waterfall) and the cost columns surfaced in tables. If Stage-2 rates change, the documented benchmark values in §3 and [`09`](09_gold_data_quality_report.md) §7 must be updated in lock-step.

Related docs:

- `08_star_schema.md` — star schema design and join map
- `09_gold_data_quality_report.md` — validation snapshot and checks
- `02_kpi_glossary.md` — measure definitions (incl. which v2 columns DAX actually reads)
