# CLAUDE.md — Power BI AI Workspace
# Commercial + Fulfilment Executive Dashboard (v1)

This file is the authoritative context for Claude Code working inside the `powerbi/` folder.
Read this before touching any file. Every section below is load-bearing.

---

## 1. Project at a glance

**Report name:** Commercial + Fulfilment Executive Dashboard (v1)
**Business goal:** Single exec-ready analytics layer covering commercial performance, discount leakage, fulfilment risk, and customer retention for a retail supply chain dataset (DataCo).
**Data rows:** ~180,519 order-line rows across FACT_SALES + FACT_FULFILMENT.
**Grain:** 1 row per `order_item_id` in all fact tables.

---

## 2. Folder structure (what lives where)

```
powerbi/
├── CLAUDE.md                                          ← this file
├── Commercial + Fulfilment Executive Dashboard (v1).pbip   ← open this in Power BI Desktop
│
├── Commercial + Fulfilment Executive Dashboard (v1).SemanticModel/
│   └── definition/
│       ├── model.tmdl           ← model-level settings, table refs
│       ├── relationships.tmdl   ← ALL relationships (active + inactive)
│       ├── expressions.tmdl     ← M parameters (pDataFolder, fnLoadCsv)
│       ├── tables/
│       │   ├── _Measures.tmdl   ← ALL DAX measures live here
│       │   ├── FACT_SALES.tmdl
│       │   ├── FACT_FULFILMENT.tmdl
│       │   ├── DIM_DATE.tmdl
│       │   ├── DIM_CUSTOMER.tmdl
│       │   ├── DIM_PRODUCT.tmdl
│       │   ├── DIM_CATEGORY.tmdl
│       │   ├── DIM_DEPARTMENT.tmdl
│       │   ├── DIM_GEO.tmdl
│       │   ├── DIM_CHANNEL.tmdl
│       │   ├── DIM_DISCOUNT_BAND.tmdl
│       │   ├── DIM_MARKET.tmdl
│       │   ├── SEC_USER_MARKET.tmdl
│       │   ├── VALIDATION_ROWCOUNTS.tmdl
│       │   └── VALIDATION_FK_COVERAGE.tmdl
│       └── roles/
│           ├── Executive.tmdl
│           └── MarketManager.tmdl
│
├── Commercial + Fulfilment Executive Dashboard (v1).Report/
│   └── definition/
│       ├── report.json          ← report-level theme + global filters
│       ├── pages/
│       │   └── pages.json       ← page order (9 pages)
│       └── pages/<page-id>/
│           ├── page.json        ← page config, canvas size, page-level filters
│           └── visuals/<visual-id>/
│               ├── visual.json  ← visual type, query, formatting, position
│               └── mobile.json  ← optional mobile layout
│
├── PBIX/
│   └── Commercial + Fulfilment Executive Dashboard (v1).pbix   ← archived original, do not edit
│
└── screenshots/                 ← reference images of all 9 pages (01.png–09.png)
```

---

## 3. Data source (how the model loads data)

**Primary path (CSV fallback — always active):**
- Source folder: `../data/databricks_gold_export/`  (relative to repo root)
- Absolute example: `D:\Projects\databricks-snowflake-medallion-pipeline\data\databricks_gold_export\`
- This path is stored as the M parameter `pDataFolder` in `expressions.tmdl`
- The helper function `fnLoadCsv` loads each CSV by name from that folder

**CSV files in that folder (one per table):**
```
dim_category.csv       dim_channel.csv        dim_customer.csv
dim_date.csv           dim_department.csv     dim_discount_band.csv
dim_geo.csv            dim_product.csv        fact_fulfilment.csv
fact_order_item.csv    fact_sales.csv
```

**Column names in CSVs are lowercase.** The semantic model maps them to UPPERCASE column names internally (Power BI auto-promotes headers).

**Snowflake (trial only — may be expired):** was the original serving layer. Not required; CSV fallback is the durable path.

---

## 4. Star schema — tables and keys

### Fact tables (grain: order_item_id)

| Table | Key columns | Measures |
|---|---|---|
| `FACT_SALES` | `order_item_id`, `order_id`, `customer_id`, `product_card_id`, `category_id`, `department_id` | `gross_sales`, `net_sales`, `profit`, `discount_amount`, `discount_rate`, `quantity`, `unit_price` |
| `FACT_FULFILMENT` | `order_item_id`, `order_id`, `customer_id`, `product_card_id`, `category_id`, `department_id` | `days_for_shipping_real`, `days_for_shipment_scheduled`, `shipping_days_variance`, `late_delivery_risk`, `is_late_by_days` |

### Dimension tables

| Table | Primary key | Notes |
|---|---|---|
| `DIM_DATE` | `DATE_KEY` (INT yyyyMMdd) | Role-playing date dimension |
| `DIM_CUSTOMER` | `CUSTOMER_ID` | Includes `First Order Date Key`, `First Purchase YearMonthSort` for cohort logic |
| `DIM_PRODUCT` | `PRODUCT_CARD_ID` | |
| `DIM_CATEGORY` | `CATEGORY_ID` | Column: `CATEGORY_NAME` |
| `DIM_DEPARTMENT` | `DEPARTMENT_ID` | Column: `DEPARTMENT_NAME` |
| `DIM_GEO` | `GEO_KEY` (xxhash64 of country+state+city) | Columns: `COUNTRY`, `STATE`, `CITY` |
| `DIM_CHANNEL` | `CHANNEL_KEY` (xxhash64 of market+region+shipping_mode) | Columns: `MARKET`, `ORDER_REGION`, `SHIPPING_MODE` |
| `DIM_DISCOUNT_BAND` | `DISCOUNT_BAND_KEY` (1–6) | Bands: 0%, >0–5%, >5–10%, >10–15%, >15–20%, >20–25% |
| `DIM_MARKET` | `MARKET` (text) | Used for RLS; 1 row per market |
| `SEC_USER_MARKET` | `UserEmail` + `MARKET` | RLS user-to-market mapping |

### Relationships (active unless noted)

| From | To | Active? | Notes |
|---|---|---|---|
| `FACT_SALES.ORDER_DATE_KEY` | `DIM_DATE.DATE_KEY` | ✅ | Primary date relationship |
| `FACT_FULFILMENT.ORDER_DATE_KEY` | `DIM_DATE.DATE_KEY` | ✅ | |
| `FACT_FULFILMENT.SHIP_DATE_KEY` | `DIM_DATE.DATE_KEY` | ❌ inactive | Use `USERELATIONSHIP()` in measures |
| `FACT_SALES.CUSTOMER_ID` | `DIM_CUSTOMER.CUSTOMER_ID` | ✅ | |
| `FACT_FULFILMENT.CUSTOMER_ID` | `DIM_CUSTOMER.CUSTOMER_ID` | ✅ | |
| `FACT_SALES.PRODUCT_CARD_ID` | `DIM_PRODUCT.PRODUCT_CARD_ID` | ✅ | |
| `FACT_SALES.CATEGORY_ID` | `DIM_CATEGORY.CATEGORY_ID` | ✅ | |
| `FACT_SALES.DEPARTMENT_ID` | `DIM_DEPARTMENT.DEPARTMENT_ID` | ✅ | |
| `FACT_SALES.GEO_KEY` | `DIM_GEO.GEO_KEY` | ✅ | |
| `FACT_SALES.CHANNEL_KEY` | `DIM_CHANNEL.CHANNEL_KEY` | ✅ | |
| `FACT_SALES.DISCOUNT_BAND_KEY` | `DIM_DISCOUNT_BAND.DISCOUNT_BAND_KEY` | ✅ | |
| `DIM_CHANNEL.MARKET` | `DIM_MARKET.MARKET` | ✅ single | Required for RLS propagation |
| `SEC_USER_MARKET.MARKET` | `DIM_MARKET.MARKET` | ✅ both | Required for RLS propagation |

---

## 5. Page directory (page folder ID → display name)

| Folder ID | Display Name |
|---|---|
| `a0a758f9a4b2a8e0ac02` | 01 Executive Overview |
| `283caca0620847149120` | 02 Revenue & Margin |
| `8b137001e2e41d290d70` | 03 Profitability Diagnostic (Sales vs Profit) |
| `5351f880ad89604a4886` | 04 Pricing & Discount Impact |
| `159c117665bd97542983` | 05 Discount Leakage Table |
| `5673b15083139526758c` | 06 Operations Overview |
| `cb3f1163e821081ef181` | 07 Operations Deep Dive |
| `78dce1045284f047998e` | 08 Customer Retention |
| `82b8adf756f284e9de9d` | 09 Data Trust & KPI Definitions |

Canvas size: **1280 × 720** (16:9), `displayOption: FitToPage` on all pages.

---

## 6. All DAX measures (in `_Measures.tmdl`)

### A. Base Commercial
- `Total Gross Sales` = SUM(FACT_SALES[gross_sales])
- `Net Sales` = SUM(FACT_SALES[net_sales])
- `Profit` = SUM(FACT_SALES[profit])
- `Quantity` = SUM(FACT_SALES[quantity])
- `Orders` = DISTINCTCOUNT(FACT_SALES[order_id])
- `Order Items` = DISTINCTCOUNT(FACT_SALES[order_item_id])

### B. Pricing & Discounts
- `Discount Amount` = SUM(FACT_SALES[discount_amount])
- `Discount Rate % (Effective)` = DIVIDE([Discount Amount], [Total Gross Sales])
- `Discount Rate % (Average)` = AVERAGE(FACT_SALES[discount_rate])

### C. Revenue & Ratios
- `Gross Margin %` = DIVIDE([Profit], [Net Sales])
- `AOV (Avg Order Value)` = DIVIDE([Net Sales], [Orders])
- `Avg Unit Price (Weighted)` = DIVIDE([Net Sales], [Quantity])
- `Profit per Order` = DIVIDE([Profit], [Orders])
- `Units per Order (Basket Size)` = DIVIDE([Quantity], [Orders])

### D. Time Intelligence (all reference DIM_DATE[date])
- `Net Sales MTD`, `Net Sales YTD`, `Net Sales LY`, `Net Sales YoY %`, `Rolling 12M Net Sales`

### E. Fulfillment
- `Fulfilment Orders`, `Late Orders (Fulfilment)`, `On-Time Orders (Fulfilment)`
- `Late Delivery Rate %`, `On-Time Delivery Rate %`
- `Avg Shipping Days (Real)`, `Avg Shipping Days (Scheduled)`, `Avg Shipping Variance`

### F. Op Severity
- `Avg Late Days (Late Orders Only)`, `% Orders Late 3+ Days`

### G. Ship Date Logic (use USERELATIONSHIP for ship date activation)
- `Late Delivery Rate % (Ship Date)`, `Fulfilment Orders (Ship Date)`

### H. Customer Logic
- `Active Customers`, `New Customers`, `Returning Customers`, `Returning Customer %`
- `Repeat Customers`, `Repeat Purchase Rate %`, `Orders per Customer`
- `Cohort Retained Customers (Selected Period)`, `Cohort Retention % (Post-Acquisition)`

### I. Advanced
- `Net Sales % of Total`, `Product Rank (Net Sales)`, `Late Delivery Rate % (3M Rolling)`
- `Shipping Gap (Days)`, `Revenue at Risk`

### L. Supply Chain Risk & Trade Spend
- `Revenue at Risk (Late SLA)`, `Estimated SLA Penalty`, `Retailer Rebate Accrual`, `True Net Profit (Post-Rebate)`

### K. Cost-to-Serve
- `Handling Cost (ABC)`, `Freight Cost (Est)`, `Total Cost-to-Serve`
- `CTS % of Net Sales`, `Net Commercial Margin`, `Net Commercial Margin %`

### J. Data Trust
- `Profitability Flag`, `Last Refresh (Sales)`, `Rows - FACT_SALES`, `Rows - FACT_FULFILMENT`
- `FK Missing Keys (Total)`, `Rank Category by Discount`

### Page title measures (dynamic market context)
`01 Executive Overview`, `02 Revenue & Margin Diagnostics`, `03 Category Profitability Map`,
`04 Pricing & Discount`, `05 Discount Leakage`, `06 Operations`, `07 Operations Deep Dive`,
`08 Customer Retention`, `09 Data Trust & KPI Definitions`

---

## 7. RLS design

**Role: Executive** — sees all markets (no filter).
**Role: MarketManager** — filtered by `SEC_USER_MARKET[UserEmail] = USERPRINCIPALNAME()`
- Filter propagates: `SEC_USER_MARKET` → `DIM_MARKET` → `DIM_CHANNEL` (via both-direction relationship)
- **Critical:** Market slicers/filters MUST use `DIM_MARKET[MARKET]`, not `DIM_CHANNEL[MARKET]`

**To test in Desktop:** Modeling → View as → MarketManager → test identity `europe_mgr@company.com`
Expected: only Europe visible in Market slicer and all visuals.

---

## 8. Global filters active on the report

- `DIM_DATE[YEAR] ≠ 2018` — report-level filter applied on all pages (2018 data excluded as partial year)

---

## 9. How Claude should edit this report

### Adding/editing a DAX measure
Edit `SemanticModel/definition/tables/_Measures.tmdl` directly.
- Follow the existing indentation (tab-based TMDL format)
- Assign a `displayFolder` matching existing groups (A. Base Commercial, B. Pricing & Discounts, etc.)
- For new measures, generate a new `lineageTag` as a UUID (any unique UUID)
- Currency measures: `formatString: \$#,0;(\$#,0);\$#,0`
- Percentage measures: `formatString: 0.00%;-0.00%;0.00%`

### Editing a visual
1. Identify the page folder ID from Section 5 above
2. Read the page's `page.json` to understand layout
3. Read `visual.json` for the specific visual
4. Edit `visual.json` directly — position, query (fields), objects (formatting)
5. Never delete `mobile.json` if it exists alongside a `visual.json`

### Adding a new visual to an existing page
- Create a new folder under the page's `visuals/` directory with a new 20-hex-char name
- Copy the structure of an existing `visual.json` of the same type as a template
- Position: use `x`, `y`, `z`, `height`, `width` in the `position` block (canvas is 1280×720)
- `tabOrder` should be higher than existing visuals on that page (increment by 1000)

### Adding a new page
1. Create a new folder under `Report/definition/pages/` with a new 20-hex-char ID
2. Add `page.json` (copy an existing page as template, update `name` and `displayName`)
3. Add the page ID to `pages.json` in the correct position in `pageOrder`
4. Create a `visuals/` subfolder for the page's visuals

### Column name casing rule
- In DAX and TMDL: column names are UPPERCASE (e.g., `FACT_SALES[NET_SALES]`)
- In CSV source files: column names are lowercase (e.g., `net_sales`)
- In visual.json query projections: use the UPPERCASE form (`"Property": "NET_SALES"`)

### What NOT to do
- Do not edit `.pbix` in `PBIX/` — it is archived
- Do not rename the `.pbip` file or the `.SemanticModel` / `.Report` folders (Power BI Desktop requires exact naming)
- Do not change relationship cardinality for RLS-related relationships (`DIM_MARKET` ↔ `SEC_USER_MARKET` must remain both-directions)
- Do not remove `pDataFolder` parameter from `expressions.tmdl` — it is how the CSV path is set
- Do not hardcode file paths in M queries — always use the `pDataFolder` parameter

---

## 10. Reload workflow (after any file edit)

1. Make changes in Claude Code (edit TMDL / JSON files)
2. In Power BI Desktop: **close the file** → reopen the `.pbip`
3. Power BI Desktop will detect file changes and reload automatically
4. If prompted about data source credentials: point to `../data/databricks_gold_export/`
5. Validate on **Page 09 — Data Trust & KPI Definitions**: row counts and FK checks must show PASS

---

## 11. Supporting docs (in `../docs/`)

| File | What it covers |
|---|---|
| `docs/02_kpi_glossary.md` | Business definitions for every KPI |
| `docs/08_star_schema.md` | Star schema grain, keys, join map |
| `docs/09_gold_data_quality_report.md` | Row counts and FK validation results |
| `docs/10_rls.md` | RLS design, role definitions, test procedure |
| `docs/11_performance_test_optimization.md` | Performance Analyzer results and Top N fix |
| `data/databricks_gold_export/` | 11 CSV files = Gold layer source data |
| `sql/gold/01_gold_build.sql` | SQL that built the Gold star schema in Databricks |

---

## 12. Project Roadmap & State

### Phase 1 — Local DevOps & Architecture Foundation ✅ COMPLETE
**Completed:** 2026-06-05

- [x] **1.1 Git version control** — Repo initialized, `.gitignore` corrected (4 bugs fixed: `*.pbi*` → explicit `*.pbix/pbit/pbiviz` to preserve `.pbip`; root-anchored `.pbi/` patterns fixed to `**/.pbi/`; `~$*` Office temp file pattern added). Baseline v1 PBIP committed on `main` (224 files, 91k lines of TMDL + JSON).
- [x] **1.2 Branching strategy** — Feature branch `feature/v2-commercial-upgrade` created. All v2 work happens here; `main` holds the stable v1 baseline.
- [x] **1.3 BPA governance (Batch 1)** — Full audit of `_Measures.tmdl`, `FACT_SALES.tmdl`, `FACT_FULFILMENT.tmdl`, `CG_TimeIntelligence.tmdl`, `relationships.tmdl`. Findings:
  - DAX DIVIDE: all 14 division operations already use `DIVIDE()` — no raw `/` operators present.
  - FK visibility: all 16 FK columns across both fact tables already carry `isHidden`.
  - formatString: fixed 2 measures missing an explicit format (`'Shipping Gap (Days)'` → `0.0`; `'Cohort Retention % (Post-Acquisition)'` → `0.00%;-0.00%;0.00%`). Stale `PBI_FormatHint isGeneralNumber` annotations removed.
  - Bi-directional RLS relationship (`SEC_USER_MARKET → DIM_MARKET`) confirmed untouched.
- Commits: `5d4f79f` (baseline), `9be242f` (BPA fixes)

---

### Phase 2 — Upstream Engineering & Rigid Data Contracts ✅ COMPLETE
**Completed:** 2026-06-05

#### 2.1 Power Query Debt Audit & Gold Layer Contract ✅
**M code debt found and resolved (4 categories):**

| # | Location | Debt removed | Resolution |
|---|---|---|---|
| 1 | `fnLoadCsv` | `Text.Trim` on headers | Gold CSVs always have clean trimmed headers from PySpark |
| 2 | Both fact partitions | `Table.TransformColumnNames(Text.Upper)` | Retained — only remaining M step; pure column-name remap, zero data mutation |
| 3 | Both fact partitions | `KeyText` block — `Number.ToText(Number.RoundDown(…))` sci-notation guard on `GEO_KEY`, `CHANNEL_KEY`, `ORDER_ZIPCODE` | PySpark casts `xxhash64()` to `StringType()` before write; sci-notation impossible |
| 4 | Both fact partitions | `Table.TransformColumnTypes` — 18-column explicit cast | Delta schema enforces types at write; M cast now a no-op (retained but inert) |

#### 2.2 Data Contract Enforcement & M Code Strip ✅
**Completed:** 2026-06-05

- `KeyText` block removed from `FACT_SALES.tmdl` (10 lines deleted)
- `KeyText` block removed from `FACT_FULFILMENT.tmdl` (11 lines deleted)
- `sql/gold/01_gold_build.sql` deprecated with header comment (PySpark is authoritative)
- `data-pipeline/01_gold_build.py` — PySpark Gold curation script with `CAST(xxhash64(…) AS StringType())` and post-write schema assertions

**Commits:** `feat: standardize Gold ETL on PySpark and strip legacy M code scientific-notation guards`

---

### Phase 3 — Advanced Commercial Semantic Modeling ✅ COMPLETE

#### 3.1 Activity-Based Cost-to-Serve (CTS) DAX Modeling ✅ COMPLETE
**Completed:** 2026-06-05

New measure folder **K. Cost-to-Serve** added to `_Measures.tmdl`:
- `Handling Cost (ABC)` = ([Orders] * 2.50) + ([Quantity] * 0.50)
- `Freight Cost (Est)` = SUMX over FACT_SALES, SWITCH on DIM_CHANNEL[SHIPPING_MODE] (Same Day $8/unit, First Class $5, Second Class $3, Standard $1.50)
- `Total Cost-to-Serve` = [Handling Cost (ABC)] + [Freight Cost (Est)]
- `CTS % of Net Sales` = DIVIDE([Total Cost-to-Serve], [Net Sales])
- `Net Commercial Margin` = [Profit] - [Total Cost-to-Serve]
- `Net Commercial Margin %` = DIVIDE([Net Commercial Margin], [Net Sales])

#### 3.2 DIFOT Financialization & Rebate Accrual ✅ COMPLETE
**Completed:** 2026-06-05

New measure folder **L. Supply Chain Risk & Trade Spend** added to `_Measures.tmdl`:
- `Revenue at Risk (Late SLA)` — [Net Sales] filtered to orders where `FACT_FULFILMENT[LATE_DELIVERY_RISK] = 1`, bridged via `ORDER_ID` set membership (no direct FK between fact tables)
- `Estimated SLA Penalty` — `[Revenue at Risk (Late SLA)] * 0.03` (3% contractual penalty)
- `Retailer Rebate Accrual` — tiered: >$5M → 5%, >$1M → 3%, else 1%; uses `SWITCH(TRUE(), ...)` pattern
- `True Net Profit (Post-Rebate)` — `[Net Commercial Margin] - [Estimated SLA Penalty] - [Retailer Rebate Accrual]`

**"Late" definition used:** `FACT_FULFILMENT[LATE_DELIVERY_RISK] = 1` (binary int64 flag, consistent with existing F/G folder measures)

### Phase 4 — Declarative UI/UX & What-If Planning ✅ COMPLETE (UI Parked)

#### 4.1 Field Parameter Table ✅ COMPLETE
**Completed:** 2026-06-05

New calculated table `Parameter_Dimensions` added to the semantic model:
- Columns: `Parameter` (text, sorted by `Parameter Order`), `Parameter Fields` (field ref), `Parameter Order` (int, hidden)
- 4 swappable axes:
  - "Product Category" → `DIM_CATEGORY[CATEGORY_NAME]`
  - "Product Department" → `DIM_DEPARTMENT[DEPARTMENT_NAME]`
  - "Shipping Mode" → `DIM_CHANNEL[SHIPPING_MODE]`
  - "Market Region" → `DIM_CHANNEL[ORDER_REGION]`
- Annotated with `ParameterMetadata = {"version":3,"kind":"Field"}` for Power BI field-parameter recognition.
- Usage: drop `Parameter_Dimensions[Parameter Fields]` onto the visual axis; add `Parameter_Dimensions[Parameter]` as the slicer.

#### 4.2 What-If Scenario Slicer ✅ COMPLETE
**Completed:** 2026-06-05

New calculated table `Scenario_FreightSurcharge` added:
- `GENERATESERIES(0, 0.50, 0.05)` — 11 values from 0% to 50% in 5% steps
- Column `Value` format: `0%`
- Harvest measure: `Selected Freight Surcharge %` = `SELECTEDVALUE(Scenario_FreightSurcharge[Value], 0)`, format `0%`, folder **L. Scenario Planning**
- `Freight Cost (Est)` measure updated: wraps base SUMX result in `* (1 + [Selected Freight Surcharge %])` so all CTS/margin measures cascade automatically.
- Annotated with `ParameterMetadata = {"version":3,"kind":"Numeric"}`.

#### 4.3 Global 9-Page Report UI/UX Redesign 🔄 IN PROGRESS (resumed 2026-06-10)
*Executing per `Docs/V2_Report_Pages_Upgrade_Plan.md` in 9 batches, one commit each.*

**Batch log:**

- [x] **Batch 1 — Field-parameter repair + measure hygiene** (commit `c630579`)
  - `Parameter_Dimensions.tmdl` rebuilt in proper field-parameter shape (named columns, column-level `ParameterMetadata` extendedProperty kind 2, `groupByColumn`, `sortByColumn`). Root cause found: the old table had auto-inferred `Value1/2/3` columns, so Desktop stripped every visual binding that referenced `Parameter Fields`.
  - Page 02 charts `84673175`/`72a1ba32`: Category axis re-added, bound to `Parameter_Dimensions[Parameter]`.
  - Page 05 bar `39747bf3`: Category re-bound to `DIM_MARKET[MARKET]`.
  - Page 07 treemap `468088c9` + pivot `1cc0fd5c`: legacy `[Revenue at Risk]` → `[Revenue at Risk (Late SLA)]` (zero legacy bindings remain report-wide).
  - **Manual verify (BLOCKING for Batch 3+):** open the `.pbip` in Desktop and confirm (1) model loads with no Parameter_Dimensions errors; (2) Page 02 Parameter slicer swaps both chart axes across the 4 dimensions; (3) Page 02 charts render with an axis again; (4) Page 07 treemap/pivot show Revenue at Risk (Late SLA) values. If Desktop strips the bindings again on save, STOP and report.

- [x] **Batch 2 — Page 01 gap fixes** (commit `71728a1`)
  - STATE slicer `0f1debf0` rebound to `DIM_CHANNEL[SHIPPING_MODE]`.
  - NEW visuals: `7b4e2f9a…` Freight Surcharge % slider, `9c1d5a3e…` Rebate Shift % slider (both range mode, Mid-Blue), `3f8a1c5e…` "WHAT-IF MODE" gold badge.
  - CTS % bar `ee8adc7e`: `xAxisReferenceLine` at 0.12, red dashed, label "CTS Target < 12%".
  - Cards: True Net Profit value Gold `#D4A843` (was green), Revenue at Risk value `#C0392B` (token-normalized). Kept the committed white-minimalist card design — the navy-card spec in `pbi_page01_instructions_by_entity.md` is an older design iteration, intentionally not applied.
  - **Manual steps needed:**
    1. **Reposition the 3 new visuals** — they overlay the CTS bar's right edge at (1186, 540–726). Page 01 canvas (1440×900) is full; drag them wherever you want the What-If panel (or shrink the scatter). Positions are out of JSON scope by design.
    2. Drag the Freight slider → waterfall CTS step, NCM % card, True Net Profit card and CTS bars must move live. Drag Rebate slider → only True Net Profit moves.
    3. Check the red dashed CTS target line renders at 12% — if invisible, the object name `xAxisReferenceLine` didn't take on your Desktop version; report back and I'll try the alternate (`referenceLineX`).
    4. Confirm the 12% threshold with the business before any exec review.

#### 4.4 Predictive Scenario Simulation (Additional Sliders) ✅ COMPLETE
**Completed:** 2026-06-08

Two new What-If parameter tables wired into existing DAX measures to build a predictive sandbox:
1. **MOQ Parameter Table (`Scenario_MOQ.tmdl`)**:
   - `GENERATESERIES(0, 100, 5)`
   - `[Selected MOQ Threshold]` harvest measure added.
   - `[MOQ Penalty Surcharge]` added to apply a $25 LTL penalty for orders below the threshold. Wired into `[Total Cost-to-Serve]`.
2. **Rebate Parameter Table (`Scenario_Rebate.tmdl`)**:
   - `GENERATESERIES(0, 0.05, 0.005)`
   - `[Selected Rebate Shift %]` harvest measure added.
   - `[Retailer Rebate Accrual]` updated to include the shift multiplier.

### Phase 5 — QA & Performance Optimization ✅ COMPLETE
**Completed:** 2026-06-08

#### 5.1 Query Benchmarking via DAX Studio
- **Test:** Stress test running `SUMMARIZECOLUMNS` with heavy iterations on `[Total Cost-to-Serve]` and `[True Net Profit (Post-Rebate)]`.
- **Result:** **164 ms Total Time**.
- **Engine Split:** FE 57.3% (94 ms) / SE 42.7% (70 ms).
- **Conclusion:** Excellent performance. No DAX rewrite needed. The complex `SUMX` models scale perfectly below the 300 ms danger threshold.

#### 5.2 RLS Leakage & Data Trust Verification
- **RLS Leakage Audit:** Verified in Power BI Desktop using "View as" with MarketManager role (`europe_mgr@company.com`). The Market slicer correctly isolates to "Europe" only. Zero data leakage verified.
- **Data Trust Verification:** Page 09 (Data Trust & KPI Definitions) visual audit confirms exactly **180,519 rows** ingested and **0 missing keys** across all dimension joins. All Green.
