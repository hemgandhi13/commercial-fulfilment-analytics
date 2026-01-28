# Power BI Report — Commercial + Fulfilment Executive Dashboard (v1)

This folder contains the **Power BI Desktop report (PBIX)** for the _Commercial + Fulfilment Executive Dashboard (v1)_.

The report is built on a **Gold star schema** (FACT + DIM tables) produced in Databricks and (optionally) served via Snowflake.  
For long-term portability, the report supports a **CSV fallback serving layer** so it remains refreshable even after Snowflake trial expiry.

---

## Folder layout

```
/powerbi/
├─ Commercial + Fulfilment Executive Dashboard (v1).pbix
├─ README.md
└─ Screenshots/
   ├─ page_01.png
   ├─ page_02.png
   └─ ...

/data/
└─ databricks_gold_export/
   ├─ FACT_SALES.csv
   ├─ FACT_FULFILMENT.csv
   ├─ DIM_DATE.csv
   ├─ DIM_CUSTOMER.csv
   ├─ DIM_PRODUCT.csv
   ├─ DIM_CATEGORY.csv
   ├─ DIM_DEPARTMENT.csv
   ├─ DIM_GEO.csv
   ├─ DIM_CHANNEL.csv
   └─ DIM_DISCOUNT_BAND.csv
```

**Paths (for reference):**

- PBIX: `\powerbi\Commercial + Fulfilment Executive Dashboard (v1).pbix`
- CSV serving layer: `databricks-snowflake-medallion-pipeline\data\databricks_gold_export`
- Screenshots: `\powerbi\Screenshots`

---

## Prerequisites

- **Power BI Desktop** (Windows)
- Local access to the CSV export folder: `data/databricks_gold_export/`

---

## Data model summary

### Grain

- Facts are at **order-line grain** (1 row per `order_item_id`).

### Tables

- **Facts**
  - `FACT_SALES` (commercial KPIs: sales, profit, discount, quantity)
  - `FACT_FULFILMENT` (operations KPIs: shipping days, variance, late risk)
- **Dimensions**
  - `DIM_DATE` _(marked as Date table)_
  - `DIM_CUSTOMER`, `DIM_PRODUCT`, `DIM_CATEGORY`, `DIM_DEPARTMENT`
  - `DIM_GEO`, `DIM_CHANNEL`, `DIM_DISCOUNT_BAND`

### Date relationships (role-playing)

- `FACT_SALES[order_date_key]` → `DIM_DATE[date_key]` **(active)**
- `FACT_FULFILMENT[order_date_key]` → `DIM_DATE[date_key]` **(active)**
- `FACT_FULFILMENT[ship_date_key]` → `DIM_DATE[date_key]` **(inactive)**
  - Ship-date analysis uses `USERELATIONSHIP()` in DAX.

---

## How to open and refresh (CSV fallback mode)

### Step 1 — Open the PBIX

Open the PBIX file from `/powerbi/`.

### Step 2 — Point Power BI to the local CSV folder

This report expects a folder-path parameter (commonly named `pDataFolder`).

1. In Power BI Desktop: **Transform data** → **Manage parameters**
2. Set the folder parameter to your local repo path, e.g.:
   - `...\databricks-snowflake-medallion-pipeline\data\databricks_gold_export`

> If your parameter name differs, search inside Power Query for the folder path step and update that value.

### Step 3 — Refresh

Home → **Refresh**

### Step 4 — Validate the refresh (mandatory)

Go to **Page 09 — Data Trust & KPI Definitions** and confirm:

- Row count tables populate (no blanks)
- FK coverage shows **0 missing keys** (PASS)
- Refresh timestamp (if present) updates as expected

---

## Optional: Snowflake serving layer (when available)

The same Gold tables can be served from Snowflake (preferred when trial access is active).  
To switch from CSV to Snowflake:

1. **Transform data** → **Data source settings**
2. Update the Snowflake connection for the Gold schema
3. Ensure table names + columns match the CSV schema contract
4. Refresh → validate on Page 09

> Credentials are not stored in the repo. Use your own Snowflake login and keep secrets out of version control.

---

## Report pages (01–09)

### 01 — Executive Overview

High-level KPIs (Net Sales, Profit, Margin %, Orders, Late Delivery Rate %) and Net Sales trend with core slicers.

### 02 — Revenue & Margin

Category/department contribution: Net Sales, Profit, Margin %, and top products.

### 03 — Profitability Map (Scatter)

Quadrant analysis (e.g., Net Sales vs Profit / Margin) to identify:

- high sales / low profit (risk)
- low sales / high profit (niche wins)

### 04 — Pricing / Discount Impact

Discount intensity vs margin outcomes and where discounting drives performance.

### 05 — Discount Leakage Table

Bottom-up leakage diagnostics by category (Net Sales, Discount Amount, Discount Rate %, Margin %).

### 06 — Operations Overview

Late delivery risk and shipping performance drivers at a market/mode level.

### 07 — Operations Deep Dive

Financial impact of fulfilment (e.g., revenue at risk) plus order-level diagnostics.

### 08 — Customer Retention / Cohorts

New vs Returning, repeat purchase behaviour, segment split, and cohort-style retention.

### 09 — Data Trust & KPI Definitions

Row counts, FK coverage checks, refresh notes, and KPI definition reference.

---

## KPI highlights (semantic layer)

Headline measures are defined in the KPI glossary and implemented in the report’s Measures table, including:

- **Commercial:** Gross Sales, Net Sales, Profit, Margin %, AOV, Discount Amount/Rate
- **Operations:** Late Delivery Rate %, Shipping Variance, On-Time Rate %
- **Customer:** Active Customers, New Customers, Returning Customers, Repeat Purchase Rate %

---

## Screenshots

Screenshots are stored in:

- `/powerbi/Screenshots/`

Recommended naming convention:

- `page_01_exec.png`
- `page_02_revenue_margin.png`
- `page_03_scatter_profitability.png`
- …
- `page_09_data_trust.png`

---

## Known scope decisions (v1)

- **CSV fallback is the default refresh mode** to keep the report portable beyond Snowflake trial.
- If you excluded partial/incomplete periods (e.g., partial year data), document that choice in Page 09 notes and keep filters consistent across pages.

---

## Troubleshooting

### Refresh fails / blank visuals

- Confirm the folder parameter points to the correct local directory
- Confirm all required CSV files exist and table names match
- Validate on Page 09 (row counts + FK coverage)

### Ship-date visuals don’t change with date slicers

- Ship date uses an **inactive relationship** by design.
- Use measures that explicitly activate it via `USERELATIONSHIP()`.

---

## Documentation references (repo root `/docs/`)

If your repo includes supporting docs, keep them linked here:

- `02_kpi_glossary.md`
- `03_data_dictionary_notes.md`
- `08_star_schema.md`
- `09_gold_data_quality_report.md`
