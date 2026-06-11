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

- [x] **Batch 2.1 — What-If hotfix after first Desktop verification round** (commit `47b4a23`)
  - Verification round 1 results: model loads ✅; Parameter slicer renders ✅ but **axis substitution NOT firing** (charts group by the parameter's literal label); sliders render but **affect nothing**; CTS reference line **not rendering**.
  - Slider root cause FIXED: `ParameterMetadata` was a table-level *annotation* on all 3 scenario tables — Power BI only honors it as a **column-level `extendedProperty`** (`{"version":0,"kind":1}` for numeric). Added to `Scenario_FreightSurcharge[Value]`, `Scenario_MOQ[MOQ_Threshold]`, `Scenario_Rebate[Rebate_Shift_Pct]`. All 4 scenario slicers switched to `'SingleValue'` mode (multi/range selection made `SELECTEDVALUE()` return 0 — that's why nothing moved).
  - Reference line: removed the schema-valid-but-not-rendering `xAxisReferenceLine` block; plan is to clone Desktop's own serialization after the user adds one constant line via the Analytics pane.
  - Field parameter substitution: TMDL survived the Desktop round-trip intact (extendedProperty + groupByColumn present). Open question is whether the metadata registers — decided by the manual test below.
  - **Manual verify round 2:** (1) reload .pbip; (2) sliders should now be single-handle sliders — set Freight to 25% on Page 01 and watch True Net Profit / NCM % / CTS bars move; (3) NEW BLANK column chart test on Page 02: drag `Parameter_Dimensions[Parameter]` to X-axis + `Net Sales` to Y — if the slicer swaps its axis, model is healthy and only the existing charts' JSON shape needs cloning from this test visual; if not, the field parameter must be recreated via Desktop UI (Modeling → New parameter → Fields) and visuals rewired to it; (4) add X-axis constant line 0.12 on the CTS bar via Analytics pane, save, leave the test visuals in place for capture.

- [x] **Batch 2.2 — Correct field-parameter binding shape captured + reference line template** (commit `3dbb323`)
  - Verification round 2 results: sliders work (user prefers Dropdown style — kept); test chart proved the model-side parameter is healthy; reference line captured from Desktop.
  - **CRITICAL PATTERN — field parameter on a visual axis (use this for all future wiring):** the projection holds a CONCRETE field (e.g. `DIM_CATEGORY[CATEGORY_NAME]`), plus a sibling `fieldParameters` array in the same role: `{"parameterExpr": {Column → Parameter_Dimensions.Parameter}, "index": 0, "length": 1}`. Never bind `Parameter_Dimensions[Parameter]` directly as a projection — that groups by the literal labels. Reference template: page 02 visual `de197928e9dd6a8eab08` (Desktop-authored test chart).
  - **CRITICAL PATTERN — constant reference line on clusteredBarChart:** object name is `y1AxisReferenceLine` (yes, even for the X-axis line on a horizontal bar; Desktop's own displayName says "X-Axis Constant Line"). `xAxisReferenceLine` is schema-valid but never renders. Properties: show/displayName/value/lineColor/transparency/style/dataLabelShow, selector id numeric string.
  - Both Page 02 charts rewired with the correct pattern; CTS line restyled token-red dashed.
  - Data-grounding for the 12% CTS threshold: portfolio CTS = $1,388,390 on $33,054,402 Net Sales = **4.20% weighted average** (handling $356k + freight $1,032k, all years, 0% surcharge). Category-level range 11%–56% (CDs/Toys are structural outliers). 12% line = "stretch target near what efficient categories already achieve"; business may prefer median (~15%).
  - **Manual verify round 3: ✅ PASSED (2026-06-10).** Both original Page 02 charts swap with the Parameter slicer; CTS reference line renders red dashed. Desktop re-serialized the fieldParameters bindings into their full materialized form: all 4 parameter fields listed as projections with `active: true/false` flags + `fieldParameters length: 4` — this is the canonical shape, even better as a template than the single-projection form.
  - **User decisions locked in:** CTS target stays at **12%** (portfolio weighted avg is 4.20%; category range 11–56%; 12% = stretch target near efficient categories). Scenario slicers stay **Dropdown** style. WHAT-IF badge textbox removed by user.
  - Page 02 test chart `de197928e9dd6a8eab08` was deleted by the user in Desktop after verification (its captured pattern lives on in the two rewired charts and commit `3dbb323`).

- [x] **Batch 3 — Field-parameter wiring pages 03–05** (commit `62b642e`)
  - Materialized fieldParameters pattern applied to: Page 03 scatter `d7870ff2` (Category), Page 04 discount-efficiency scatter `6cc9f387` (Category), Page 05 leakage table `9a9e6bca` (first Values column). Default field = Product Category, all 4 fields listed with active flags.
  - All four Parameter slicers (`a1b2c3d4` p02, `b2c3d4e5` p03, `c3d4e5f6` p04, `d4e5f601` p05): single-select enforced, "View By" 9pt header, white bg, `#E2E8F0` border. Positions untouched (p02 in left rail, p03–05 top-right).
  - **Manual verify (gates Batch 4):** reload .pbip, then on each of pages 03/04/05 use the "View By" slicer: p03 scatter dots regroup, p04 scatter regroups, p05 table's first column swaps between Category/Department/Shipping Mode/Region. With nothing selected all default to Product Category. Check the p05 table still shows its 4 measure columns after the swap.

- [x] **Batch 3 verified by user ✅** — user also added Desktop polish (leakage data bars, margin colour scale, p03 scatter break-even reference lines), committed in `df98e92`.

- [x] **Batch 4 — Page 02 NCM surfaces + KPI strip** (commit `984df45`)
  - NEW KPI cards `b4a2c8e1`/`c5b3d9f2`/`d6c4eaf3`/`e7d5fb04`: Net Sales, Profit, Gross Margin %, **Net Commercial Margin % (gold)** — temp overlay strip at y100, x128–1244, 270×84 each.
  - `72a1ba32` margin chart: `[Net Commercial Margin %]` second series, retitled "Gross vs Net Commercial Margin % (post-CTS)".
  - `59621fea`: `[Net Commercial Margin]` second series, retitled "Profit vs Net Commercial Margin by Department".
  - `710ebe38` Top 10 Products: `[Total Cost-to-Serve]` + `[Net Commercial Margin]` columns appended.
  - `84673175` retitled "Net Sales by Selected Dimension".
  - **Manual steps:** (1) reposition the 4 new KPI cards — they overlay the top of both big charts; make room by shrinking charts or arranging the strip between title and charts; (2) verify both margin/profit charts show two series with a legend and the gap between gross and NCM bars reads clearly; (3) Top-10 table shows 6 columns; widen the visual if cramped; (4) optional: add red-tint conditional formatting on the Net Commercial Margin column via Desktop UI (Format → Cell elements → Background color rules) — rule-based fills are best authored in Desktop.

- [x] **Batch 4.1 — verification feedback fixes** (commit `186d915`)
  - p02 KPI cards recoloured `#0F172A` to match Page 01 standard (colour rule: ink `#0F172A` for all standard measures, Gold `#D4A843` only for True Net Profit, Red `#C0392B` only for Revenue at Risk / SLA Penalty).
  - All 4 View By slicers: baked-in default selection "Product Category" via `general.filter` In-condition — clearing the slicer now returns charts to the default dimension.
  - Top 10 table: removed accidental Net Sales background gradient (user's conditional-format attempt saved as gradient on wrong field).
  - **Clarified behaviours (by design, not bugs):** only the 2 "Selected Dimension" charts swap on p02 (Profit by Department + Top 10 are intentional static anchors); KPI cards never react to the View By slicer because field parameters swap grouping axes, they do not filter data.
  - **Outstanding manual step:** re-author the negative-NCM rule in Desktop — select Top 10 table → Format → Cell elements → series **Net Commercial Margin** → Background color → Rules → base it on **Net Commercial Margin**, rule `>= Min(0 Percent) and < 0 (Number) → #C0392B-tinted red`. The user's rule bounds were correct; only the base field was wrong. After saving, capture the serialization as the rules-template for pages 05/07/08.

- [x] **Batch 4.2 — rules template captured** (commit `9b4e31f`)
  - User re-authored the negative-NCM rule correctly in Desktop; Top 10 table now tints Net Commercial Margin cells red (`#EF4444`) when < 0.
  - **CRITICAL PATTERN — rule-based conditional formatting (third captured template):** `objects.values[].properties.backColor.solid.color.expr` = `"Conditional": {"Cases": [{"Condition": {"Comparison": {"ComparisonKind": 3, "Left": {Measure…}, "Right": {"Literal": "0D"}}}, "Value": {"Literal": "'#EF4444'"}}]}` with selector `{"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": "_Measures.<column>"}`. ComparisonKind 3 = less-than. Reference: p02 visual `710ebe38`. Use for pages 05/07/08 conditional fills — no Desktop round-trip needed anymore.
  - Colour note: user's rule uses `#EF4444`; token alert red is `#C0392B` — consider a softer tint (`#F5D7D3`) for cell backgrounds during the Batch 9 sweep if readability suffers.

- [x] **Batch 5 — Page 03 CTS diagnostic** (2026-06-11)
  - Scatter `d7870ff2`: Y rebound `[Profit]` → `[Net Commercial Margin]`; tooltips +`[Total Cost-to-Serve]` +`[CTS % of Net Sales]`; retitled "Net Sales vs Net Commercial Margin (post-CTS)"; existing Desktop-authored `y1AxisReferenceLine` relabelled "Break-even (NCM = 0)" and given explicit `value: 0D` (it had none); width 1136 → 744 to open a right-hand column.
  - `Scatter Color Code` measure (only used by this scatter) repointed: `IF([Net Commercial Margin] < 0, "#C0392B", "#2960A8")` — dot colours now flag post-CTS unprofitability in token colours.
  - KPI strip rebound to CTS P&L: `184cd6c2` → Total Cost-to-Serve, `f676e4ed` → Handling Cost (ABC), `23e501fb` → Freight Cost (Est), `32bf540d` → CTS % of Net Sales. First three get ink `#0F172A` values (p02 parity); CTS % card gets Conditional font colour (Red `#C0392B` > 12%, Gold `#D4A843` 9–12%, ink < 9%) via the Batch 4.2 Cases template.
  - Textbox `84ea4a36`: 3,500-line auto-generated smart narrative replaced with a static textbox (CTS formula copy + bubble-click tip). Styling limited to bold runs — textRun fontSize/colour shapes were never captured from Desktop, so not guessed.
  - STATE slicer `8d9eb224` rebound → `DIM_CHANNEL[SHIPPING_MODE]` (WS-3).
  - NEW `c7e9f1a3…` stackedBarChart "Cost-to-Serve Composition" at (880, 256) 384×464: materialized fieldParameters Category (default Product Category) + Handling (ink) / Freight (Mid-Blue) series, legend top, sorted by Freight desc.
  - NEW `d9f1a3b5…` Freight Surcharge % slicer at (0, 576) 128×96 in the left rail — clone of the p01 dropdown slicer incl. baked-in 0% default. No WHAT-IF badge (user removed the p01 one).
  - **Manual verify (gates Batch 6):** (1) reload .pbip; (2) scatter Y axis reads Net Commercial Margin, red dots sit below the 0-line, break-even line renders; (3) drag Freight Surcharge to 25% — scatter dots, CTS composition bars and all 4 KPI cards must move; (4) CTS % card font flips colour (portfolio ~4.2% = ink; slide freight up to force Gold/Red); (5) View By slicer swaps both the scatter AND the new composition bar; (6) layout check — scatter/bar split at x872/880 may need a nudge; (7) series colours on the stacked bar (ink+blue) — if defaults show instead, the `selector.metadata` shape needs Desktop capture.

- [x] **Batch 5.1 — verification feedback fixes** (2026-06-11)
  - **CustomVisualNotFound root cause:** `stackedBarChart` is NOT a built-in visualType (Desktop hunts for a custom visual by that name). The built-in stacked bar is **`barChart`** (clustered = `clusteredBarChart`; stacked column = `columnChart`). `c7e9f1a3…` fixed. Add to the never-guess list: built-in visualType names are not always the Desktop UI label.
  - Desktop's re-save normalized the p03 scatter's fieldParameters back to single-projection form (`length: 1`) — binding intact, both materialized and single forms are valid.
  - **Clarified (by design, not bugs):** Handling Cost (ABC) card ignores the freight slider — handling = $2.50/order + $0.50/unit, surcharge only scales freight. CTS % card colour can't flip at portfolio level (4.20% base, ~5.8% even at +50% freight — still ink); it flips when filtered to a high-CTS category (CDs ≈ 56% → red).
  - **NEW STANDARD (user decision): every KPI card carries page-logic conditional font colour, reacting to slicers/filters.** Rolled out to pages 01–02 using break-even thresholds only (no invented business numbers):
    - p01 `daa20507` True Net Profit: < 0 red, else Gold. `4e0bb205` Revenue at Risk: > 0 red, else ink. `dac3aef3` NCM %: < 0 red, else ink. (Net Sales / Gross Sales cards: no defensible threshold, stay ink.)
    - p02 `c5b3d9f2` Profit, `d6c4eaf3` Gross Margin %, `e7d5fb04` NCM %: < 0 red, else ink. (Net Sales stays ink.)
    - p03 already done in Batch 5 (CTS % Red/Gold/ink; $-cost cards have no threshold, stay ink).
    - Batches 6–8 MUST apply the same per-page conditional logic to their KPI cards (p04 discount cards; p06/07 late-rate cards need the ~30% SLA threshold — still awaiting business confirmation; p08 retention cards).
  - **Manual verify:** (1) p03 composition bar now renders as a built-in stacked bar with ink/blue series; (2) p01: filter to a loss-making slice (e.g. CATEGORY = CDs) — True Net Profit flips Gold→red, NCM % flips ink→red; (3) p02: same filter test on Profit/GM%/NCM% cards; (4) p03 CTS % card: set CATEGORY to CDs → red.

- [x] **Batch 5 + 5.1 verified by user ✅** (2026-06-11). Composition bar renders as built-in stacked bar; conditional card colours confirmed.

- [x] **Batch 6 — Page 04 promotional ROI** (2026-06-11)
  - Scatter `6cc9f387`: +Tooltip `[Net Commercial Margin %]`; the existing Desktop-authored X-axis **average** `referenceLine` (generic object name with `Aggregation` value expr — better captured pattern than a hard-coded constant) restyled gold dashed, renamed "Portfolio Avg Discount Rate". Data note: median per-category effective discount rate = 10.14% = portfolio avg (tight 8.8–11.1% range), so avg ≈ median — dynamic line preferred over static.
  - `18af6441` Revenue Mix: flat fill → Mid-Blue `#2960A8`; data labels in $M (`labelDisplayUnits 1000000D`).
  - `20ef5e69` Margin Erosion: +`[Net Commercial Margin %]` second series; GM% series Mid-Blue, NCM% series Conditional (< 0 Alert Red, else Gold) via selector metadata; legend top.
  - `f14c0b01` Profit Capture: per-bar Conditional fill (`[Profit]` < 0 red, else Mid-Blue) with dataViewWildcard selector; data labels already on; fixed stray quote in title.
  - Cards: `78d5c340` rebound Profit → `[Discount Amount]` (strip now reads Net Sales · Discount Amount · Gross Margin % · Discount Rate %). Page-logic conditionals: Net Sales + Discount Amount ink; Gross Margin % < 0 red; Discount Rate % ≥ 20% red (deepest-band boundary) / ≥ 12.5% gold (plan §6 colour-scale midpoint) / else ink.
  - `ac88471b` STATE slicer rebound → `DIM_CHANNEL[SHIPPING_MODE]` (WS-3).
  - Discount trend combo chart DEFERRED: page is full (scatter + 3 columns + strip + rails); plan §5 fallback applies — Page 05's area chart (Batch 7) carries the trade-spend trend.
  - **Manual verify (gates Batch 7):** (1) reload; (2) scatter: gold dashed avg-discount line renders, tooltip shows NCM %; (3) Margin Erosion: two series with legend, deepest band (>20–25%) NCM% bars red (filter to a category like CDs if portfolio-level NCM% is positive everywhere); (4) Profit Capture: negative bands red / positive Mid-Blue; (5) Revenue Mix single Mid-Blue with $M labels; (6) card strip: Discount Amount card present, Discount Rate % card ink at ~10% — filter to deep-discount slice to see gold/red; (7) View By still swaps the scatter.

- [x] **Batch 6 verified by user ✅** (2026-06-11) — one finding: Discount Rate % card thresholds unreachable (dataset range 8.8–11.1%). Fixed in `a894c0d`: gold ≥ 10% (above 10.14% portfolio avg), red ≥ 12.5%. **Threshold lesson: validate conditional-formatting thresholds against actual data ranges before picking them** (compute from the Gold CSVs).

- [x] **Batch 7 — Page 05 discount leakage forensic** (2026-06-11)
  - Table `9a9e6bca`: appended `[Retailer Rebate Accrual]` column (now 6 cols: dimension + Net Sales, Discount Amount, Discount Rate %, Gross Margin %, Rebate Accrual). User's Desktop polish already covered data bars on Discount Amount (orange `#eb895f` — kept), GM% white→orange colour scale, sort by Discount Amount desc, Top-20 rank filter — none re-authored.
  - **FOURTH CAPTURED PATTERN — gradient colour scale (`FillRule`):** `objects.values[].properties.backColor.solid.color.expr.FillRule` = `{"Input": {Measure…}, "FillRule": {"linearGradient2": {"min": {"color": {Literal}}, "max": {"color": {Literal}}, "nullColoringStrategy": {"strategy": {Literal 'asZero'}}}}}` with selector `{data: [dataViewWildcard 1], metadata: "_Measures.<measure>"}`. Desktop-authored on this table (GM% scale). Cloned for Discount Rate %: white → `#C0392B` data-relative scale (chose the captured 2-stop shape over guessing linearGradient3-with-thresholds serialization).
  - Bar `39747bf3` Leakage by Market: per-bar Conditional fill keyed to `[Discount Rate % (Effective)]` — same thresholds as the p04 card (≥ 12.5% red, ≥ 10% gold, else Mid-Blue).
  - Area `9fd5be75`: `[Retailer Rebate Accrual]` second series (Gold) alongside Discount Amount (now explicit Mid-Blue) = total trade-spend trend (also fulfils the p04 deferred trend slot). Existing max/avg reference lines untouched (selector-scoped to Discount Amount).
  - Cards: `5f544d3e` rebound Gross Margin % → `[Retailer Rebate Accrual]` (Gold value); `42e66771` Net Sales + `e388e506` Discount Amount → ink (no defensible $ thresholds).
  - STATE slicer `5da75b6e` rebound → `DIM_CHANNEL[SHIPPING_MODE]` (WS-3).
  - **Manual verify (gates Batch 8):** (1) reload; (2) table shows Rebate Accrual column + red-tint scale on Discount Rate % (relative: worst rows darkest); (3) market bars coloured by discount rate (most should be Mid-Blue/gold at ~10%); (4) area chart shows gold rebate series under the blue discount area, legend distinguishes; (5) Rebate Accrual card gold; (6) View By still swaps the table's first column.

**▶ NEXT SESSION — verify Batch 7 in Desktop, then Batch 8** (Pages 06/07 operations per plan §7–8 — **BLOCKED INPUT: ~30% SLA-breach threshold for late-rate conditionals still unconfirmed by business**; proceed with break-even-style defensible thresholds where possible and leave SLA-dependent rules pending if unanswered) then Batch 9 (p08 retention + p09 + report-wide sweep incl. p02 STATE slicer `0af6b5f7` → SHIPPING_MODE). (Page 04 promotional ROI: margin-erosion chart second series `[Net Commercial Margin %]` + Alert-Red conditional, profit-capture conditional colours, card rebind `78d5c340` → `[Discount Amount]`, STATE slicer → SHIPPING_MODE, median-discount reference line on the scatter, optional discount trend combo) per `Docs/V2_Report_Pages_Upgrade_Plan.md` §5. Then Batches 7–9 in order, one commit per batch, Desktop verify between. Remaining business input: ~30% SLA-breach threshold (Batch 7) still unconfirmed. Note: p02 STATE slicer `0af6b5f7` → SHIPPING_MODE (WS-3) was never done in Batch 4 — fold into Batch 9 sweep.

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
