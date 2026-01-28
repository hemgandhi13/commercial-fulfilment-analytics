# 03 — Data Dictionary Notes (Gold Layer, Databricks)

This document defines the **Gold star schema contract** produced in **Databricks** for the Dataco Supply Chain dataset.
It is intentionally **Databricks-first**: table grain, keys, and column meanings as implemented in the Gold layer.

**Gold schema location (Databricks):** `workspace.gold`  
**Declared grain:** Facts are at **order-line grain** → **1 row per `order_item_id`**.

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

### Facts

- `gold.fact_sales`
- `gold.fact_fulfilment`

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
- `fact_sales`: 180,519
- `fact_fulfilment`: 180,519

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
4. Core KPI driver columns: `gross_sales`, `net_sales`, `profit`, `discount_amount`, `discount_rate`, shipping-day fields, `late_delivery_risk`

Related docs:

- `08_star_schema.md` — star schema design and join map
- `09_gold_data_quality_report.md` — validation snapshot and checks
