# Commercial + Fulfilment Executive Dashboard (v1)

## Databricks → Snowflake (trial serving layer) → Power BI

with CSV fallback for durability after trial expiry.

End-to-end analytics build that takes raw retail + fulfilment data through a **medallion pipeline (Bronze → Silver → Gold)** in **Databricks Free Edition**, models it as a **star schema**, and delivers a **Power BI executive dashboard** covering commercial performance, discount leakage, fulfilment risk, and customer retention.

> **Important:** Snowflake was used as the primary “serving layer” during the trial window.  
> To keep this project durable after the trial ends, the report supports a **CSV fallback serving layer** (Gold exports loaded into Power BI).

---

## Summary

- **Business problem:** quantify **commercial performance**, identify **discount leakage**, monitor **fulfilment risk**, and track **customer retention** with a single executive-ready model.
- **Stack:** **Databricks (Bronze/Silver/Gold)** → **Snowflake (trial serving layer)** or **CSV Gold exports (durable fallback)** → **Power BI (star schema + DAX KPI pack)**.
- **Deliverable:** a **9-page Power BI executive dashboard** with **data trust checks**, **market-level RLS**, and **performance validation**.

---

## Key features (capabilities shipped)

- **Star schema semantic model** (facts + conformed dimensions) powering all pages consistently
- **DAX KPI pack** across commercial, pricing/discount, operations, and retention
- **Data trust checks** (row counts + FK coverage) plus KPI definitions and refresh notes
- **Security:** Market-level **Row-Level Security (RLS)** using a user-to-market mapping table (`SEC_USER_MARKET`)
- **Performance discipline:** tested with **Performance Analyzer**; optimisation documented (Top N on leakage table)
- **Durable refresh design:** Snowflake during trial + **CSV fallback** to keep the report usable after trial expiry

---

## What this delivers

### Business questions answered

- **Commercial performance:** Which markets, departments, categories and products drive **net sales vs profit**?
- **Profitability structure:** Where do we have **high sales but low profit** (quadrant analysis)?
- **Discount effectiveness:** Where is discounting improving outcomes vs **eroding margin**?
- **Discount leakage:** Which categories/markets are giving away the most **discount $**?
- **Fulfilment risk:** Where is **late delivery** concentrated and which shipping modes/markets drive risk?
- **Retention:** Are customers returning, and which cohorts retain best?
- **Trust & governance:** Are the KPIs backed by **validated keys and row counts**?

### Engineering signals

- Databricks medallion pipeline with curated **Gold star-schema tables**
- Dimensional modelling (facts + conformed dimensions + date role handling for ship date)
- Data quality checks (row counts + FK missing key checks)
- Row-Level Security (RLS): **MarketManager** role using `SEC_USER_MARKET` mapping (market-level access control)
- Semantic model governance: slicers wired to **dimension tables** (e.g., `DIM_MARKET[MARKET]`) to ensure consistent filtering + RLS propagation
- Performance validation: Power BI **Performance Analyzer** runs captured for key pages/visuals
- GitHub-ready documentation pack (BI brief, KPI glossary, data dictionary notes, QA reports)

---

## KPI Pack (core measures)

### Commercial

- Net Sales
- Profit
- Gross Margin %
- Orders
- Net Sales / Profit by Market, Department, Category, Product
- Profitability quadrants (Sales vs Profit)

### Pricing & discount

- Discount $
- Discount Rate
- Discount impact vs margin/profit outcomes
- Discount leakage (ranked) + leakage trend

### Operations / fulfilment

- Late Delivery %
- On-time Delivery %
- Shipping Days (Scheduled vs Actual)
- Delay distribution by Market / Shipping Mode
- Revenue at Risk (delayed shipments / delayed orders)

### Retention

- New vs Returning Customers
- Returning Customer %
- Retention trend
- Cohort table (first purchase month logic)

---

## Data model contract (star schema at a glance)

**Primary grain**

- Commercial facts: **order line / order-level commercial outcomes** (Net Sales, Profit, Discount metrics)
- Fulfilment facts: **shipment / delivery outcomes** (late delivery, shipping days, delay drivers)

**Facts**

- `FACT_SALES`
- `FACT_FULFILMENT`

**Conformed dimensions**

- `DIM_DATE` (role-playing for different date contexts)
- `DIM_CUSTOMER`
- `DIM_PRODUCT`
- `DIM_CATEGORY`
- `DIM_DEPARTMENT`
- `DIM_GEO`
- `DIM_CHANNEL`
- `DIM_MARKET`
- `DIM_DISCOUNT_BAND`

**Date role handling**

- **Order Date** is the active relationship for commercial trends.
- **Ship Date** is handled via an inactive relationship activated in measures using `USERELATIONSHIP()` where required.

Full model notes: `docs/08_star_schema.md`

---

## Data quality results (trust checks)

The report includes a dedicated **Data Trust & KPI Definitions** page with validation outputs.

- Gold model row counts: **~180,519 rows** (core fact table total)
- FK coverage checks: **target = 0 missing keys**, achieved **0** in the validated Gold export set
- Standardisation rules (applied in Silver/Gold):
  - type enforcement + null handling for key columns
  - de-duplication where required
  - consistent key formatting to preserve joins

(See: Page **09 Data Trust & KPI Definitions** + `docs/09_gold_data_quality_report.md`)

---

## Architecture

1. **Databricks Free Edition**

- Bronze: ingestion + raw audit
- Silver: cleaned/standardised entities
- Gold: curated fact/dim tables + star schema + quality checks

2. **Serving layer**

- **Primary (during trial):** Snowflake Gold tables (semantic serving layer)
- **Fallback (durable):** CSV exports of Gold tables loaded into Power BI

3. **Power BI Desktop**

- Imports Gold tables (Snowflake or CSV fallback)
- Measures & KPI logic (commercial, fulfilment, retention)
- Executive dashboard pages + QA/definitions page

---

## Power BI report

**Report:** Commercial + Fulfilment Executive Dashboard (v1)  
**Power BI assets:** see **`/powerbi/`** (includes PBIX + screenshots + a Power BI-specific README)

### Pages included (v1)

**01) Executive Overview** — top-line KPIs + trends + market/category views  
![Executive Overview](powerbi/screenshots/01.png)

**02) Commercial Breakdown** — product/category/department performance  
![Commercial Breakdown](powerbi/screenshots/02.png)

**03) Profitability Scatter** — net sales vs profit (quadrant analysis)  
![Profitability Scatter](powerbi/screenshots/03.png)

**04) Pricing & Discount Impact** — discount rate/amount vs margin/profit outcomes  
![Pricing & Discount Impact](powerbi/screenshots/04.png)

**05) Discount Leakage Table** — categories giving away the most discount $  
![Discount Leakage Table](powerbi/screenshots/05.png)

**06) Operations Overview** — late delivery trend, risk by market, scheduled vs actual days  
![Operations Overview](powerbi/screenshots/06.png)

**07) Operations Deep Dive** — revenue at risk + delay drivers + market table  
![Operations Deep Dive](powerbi/screenshots/07.png)

**08) Customer Retention** — new vs returning + retention trend + cohorts  
![Customer Retention](powerbi/screenshots/08.png)

**09) Data Trust & KPI Definitions** — row counts, FK checks, KPI definitions, refresh notes  
![Data Trust & KPI Definitions](powerbi/screenshots/09.png)

---

## Repo structure (artifacts & proof pack)

```text
/powerbi/
  Commercial_Fulfilment_Executive_Dashboard_v1.pbix
  README.md
  /screenshots/
    01.png
    02.png
    ...
/data/
  /databricks_gold_export/
    FACT_SALES.csv
    FACT_FULFILMENT.csv
    DIM_DATE.csv
    DIM_CUSTOMER.csv
    DIM_PRODUCT.csv
    DIM_CATEGORY.csv
    DIM_DEPARTMENT.csv
    DIM_GEO.csv
    DIM_CHANNEL.csv
    DIM_MARKET.csv
    DIM_DISCOUNT_BAND.csv
/docs/
  rls.md
  rls_demo.mp4
  performance.md
  01_bi_brief.md
  02_kpi_glossary.md
  03_data_dictionary_notes.md
  04_ingestion_log.md
  05_silver_layer_story.md
  06_data_quality_report.md
  07_engineering_notes_errors_and_decisions.md
  08_star_schema.md
  09_gold_data_quality_report.md
```

## Reproducibility runbook (serving layer options)

### Option A — Snowflake serving layer (trial active)

1. Ensure Gold tables/views exist in Snowflake (same schema/columns as documented in `docs/08_star_schema.md`).
2. Power BI Desktop → configure the Snowflake connector to the Gold schema.
3. Refresh → validate KPIs populate as expected.

### Option B — CSV fallback (durable)

Use the Quick start steps below to point the PBIX to `data/databricks_gold_export`.

---

## Quick start (CSV fallback – durable)

1. **Open the PBIX**

- `powerbi/Commercial_Fulfilment_Executive_Dashboard_v1.pbix`

2. **Point Power BI to the CSV export folder**

- Repo-relative folder: `data/databricks_gold_export`

3. **Refresh the model**

- Power BI Desktop → **Home → Refresh**
- If prompted for a folder/parameter, select your local path:
  - `<your-local-repo-path>/data/databricks_gold_export`

4. **Test RLS (optional)**

- Modeling → **View as** → **MarketManager**
- Enter test user (e.g., `europe_mgr@company.com`)
- Confirm visuals restrict to that market

✅ The report should load using the Gold CSV exports.

---

## Notes on Snowflake vs CSV fallback (schema contract)

- **Snowflake (primary):** used as the serving layer while the trial is active.
- **CSV fallback (durable):** keeps the dashboard refreshable after Snowflake access expires.
- **Schema contract matters:** CSV filenames + column names + data types must match the Gold schema so measures don’t break.
- Gold schema definition: `docs/08_star_schema.md`

---

## Row-Level Security (RLS) — Market-based access

### Tables

- `DIM_MARKET`  
  Unique list of markets (1 row per market)
- `SEC_USER_MARKET`  
  User-to-market mapping table  
  Columns: `UserEmail`, `MARKET`

### Relationships (required)

- `DIM_MARKET[MARKET] (1) → DIM_CHANNEL[MARKET] (*)`  
  Cross-filter: **Single** | Active: ✅
- `DIM_MARKET[MARKET] (1) ↔ SEC_USER_MARKET[MARKET] (*)`  
  Cross-filter: **Both** | Active: ✅  
  Purpose: allow the **MarketManager** RLS filter (on mapping table) to propagate into the model.

### Report wiring requirement

Market slicers/filters must use:

- `DIM_MARKET[MARKET]` (not `DIM_CHANNEL[MARKET]`)

### Validation (Power BI Desktop)

Modeling → View as → **MarketManager**  
Test identity: `europe_mgr@company.com`

Expected:

- Only **Europe** available in Market slicer
- All visuals restricted to **Europe** data
- Executive role shows all markets

Full RLS notes: `docs/rls.md`

---

## Performance & optimisation notes (Power BI Desktop)

Performance validated using **Performance Analyzer** on the Discount Leakage page(s).

Typical visual render times observed:

- Slicers: ~70–90 ms
- Charts/cards: ~180–270 ms
- Table visual: ~230–283 ms  
  Breakdown (table): DAX query ~15–25 ms, visual display/render ~160 ms, remaining time = Power BI overhead/other

Optimisation applied:

- Discount leakage table uses **Top N filtering** to constrain the result set and reduce visual render cost while preserving decision value.

Performance notes: `docs/performance.md`

---

## Publishing / Sharing

Power BI Service publishing requires a **work/school account**. Since this project is built and demonstrated in Power BI Desktop, sharing is provided via:

- PBIX (`/powerbi/`)
- Full screenshots of all pages (`/powerbi/screenshots/`)
- RLS + performance documentation (`docs/rls.md`, `docs/performance.md`)

This ensures the project is reviewable without Power BI Service access.

---

## Assumptions, limitations, and next iteration (v1 → v2)

### Assumptions

- Gold exports are treated as the source-of-truth contract for the Power BI semantic model.
- Market-level access control is enforced via the `SEC_USER_MARKET` mapping table + RLS role design.

### Limitations (v1)

- Snowflake is used as a trial serving layer only; long-term use requires a paid account.
- Power BI Service publishing is not included due to account constraints (work/school sign-in requirement).
- Refresh is performed via Desktop against either Snowflake (trial) or local CSV exports.

### Next iteration (v2)

- Parameterised environment switching (Snowflake ↔ CSV) with documented “one-click” refresh flow
- Incremental refresh strategy (where supported) and dataset size optimisation
- More performance tuning on heavy visuals (reduce overdraw, optimise table rendering, tighten filters)
- CI workflow for versioning Power BI artefacts (PBIP where applicable)

---

## Documentation (proof pack)

All supporting project notes live in `docs/`:

- BI brief (stakeholder goals + KPI contract)
- KPI glossary (metric definitions)
- Data dictionary notes (tables, grain, keys, pitfalls)
- Ingestion + Silver story + QA reports
- Engineering decisions & errors log
- Gold data quality report
- RLS design + validation
- Performance validation notes

### Star schema (semantic model)

![Star schema model](powerbi/screenshots/model_star_schema.png)

Power BI-specific usage notes: `powerbi/README.md`
