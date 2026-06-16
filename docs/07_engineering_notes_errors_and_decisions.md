# Engineering Notes — Errors, Decisions, and Fix Patterns

This document summarises the non-trivial engineering issues encountered building the project, and how they were resolved. The intent is to demonstrate reproducible problem-solving and “enterprise-safe” decision-making.

- **Part A — Silver layer (v1 foundations):** §1–§7 below.
- **Part B — v2 commercial upgrade:** semantic-modelling, data-provenance, and report-layer decisions (the v2 lessons that are otherwise only in the local AI workspace).

---

## Part A — Silver Layer (v1)

## 1) PII Exclusion (Enterprise Safety)

**Problem:** The raw dataset contained sensitive customer fields that should not exist in analytics layers.

**Decision:** Exclude PII from Silver and all downstream layers.

- `customer_email`
- `customer_password`
- `customer_street`
- `customer_fname`, `customer_lname`

**Rationale:** Analytics layers should be safe-by-default and aligned with common enterprise governance expectations. If personal identifiers are required for a controlled use case, they should be handled in a separate restricted dataset, not in BI-ready layers.

---

## 2) Timestamp Parsing with Inconsistent Formats

**Problem:** Date/time fields arrived as strings with inconsistent formats.

- Example patterns observed: `M/d/yyyy H:mm` and `MM/dd/yyyy HH:mm`

**Decision:** Parse using dual-format `COALESCE` and retain raw fields.

- Keep raw: `order_ts_raw`, `ship_ts_raw`
- Parsed: `order_ts`, `ship_ts`
- Derived: `order_date`, `ship_date`

**Rationale:** Keeping both raw and parsed supports auditability and makes data-quality issues diagnosable.

---

## 3) Standardisation vs “No Change” Confusion (v2)

**Observation:** Many rows appear unchanged when comparing raw vs standardised fields (v2), which can look pointless at first glance.

**Clarification:** Standardisation is still valuable because:

- it guarantees consistent whitespace and case rules
- it prevents join fragmentation in downstream dims/facts
- it creates canonical key strings for hashing and deterministic joins

Even if 80–90% of values are unchanged, standardisation prevents downstream issues for the remaining fraction.

---

## 4) Replacement Character `�` (Encoding Corruption)

**Problem:** Many countries/cities contained `�`, indicating encoding corruption (data loss).

- Example: `M�xico`, `Espa�a`, `Berl�n`

**Decision:** Do not attempt unsafe automatic fixes or guess accents.
Use a controlled mapping table:

- `silver.ref_text_fixes(field, bad_value, good_value)`
  and apply it to produce clean display columns and clean keys (v3).

**Rationale:** Encoding corruption is not reliably reversible from the corrupted value alone. A reference-driven approach is auditable, deterministic, and aligns with enterprise master-data practices.

---

## 5) SQL MERGE Constraints in Databricks (Syntax Gotchas)

**Issue:** Databricks SQL / Delta MERGE surfaced constraints:

- “Column aliases not allowed in MERGE” for certain patterns
- errors when referencing columns not present in the target schema (e.g., using `domain` when the table column is `field`)

**Fix Pattern Used:**

- Avoid aliasing the target table
- Use `USING (SELECT col1,col2,col3 FROM VALUES ...) s` pattern
- Align join keys to real target column names (`field`, not `domain`)

**Rationale:** This is a platform-specific constraint; documenting it demonstrates execution maturity.

---

## 6) High NULL Rate in Zipcodes (155,679 / 180,519)

**Problem:** `order_zipcode` was NULL for a large portion of rows.

**Decision:** Treat as a source-data property; do not impute.
Downstream dimensional modelling uses:

- NULL-safe key construction (coalesce + hashing patterns)

**Rationale:** Zipcodes are often missing in real operational datasets. Imputation can create false precision and breaks governance. Instead, build dims/facts that are robust to missing geo granularity.

---

## 7) Why Silver “Current” Exists

**Decision:** Always expose a stable downstream contract:

- `silver.dataco_supplychain_clean_current`

**Rationale:** Downstream layers (Gold, BI semantic models, Snowflake replication scripts) should not be rewritten when Silver evolves. Only the “current” pointer changes.

---

## Part B — v2 Commercial Upgrade

These decisions span the upstream enrichment, the DAX semantic model, and the PBIR report layer. They are recorded here because the detailed build log lives in a **git-ignored** local workspace (`powerbi/Docs/`) — without this section the public repo would lose them.

### B1) Benchmark-modelled enrichment, transparently labelled

**Problem:** A credible commercial story (cost-to-serve, freight, SLA penalties, rebates) needs cost attributes DataCo simply does not contain.

**Decision:** Add them as an explicit, **deterministic (seed-42)** enrichment stage (`02_gold_schema_remediation.py`) modelled on FMCG/retail benchmarks, and **label every synthesized field** as such across the docs and a self-reported PASS/MOCKED matrix.

**Rationale:** Mirrors how real cost-to-serve programmes bootstrap from benchmarks before activity actuals arrive. The honesty is the point — the *methods* are production-grade; the *rates* are stand-ins. Hiding that would be the failure mode. (See [`03`](03_data_dictionary_notes.md) §6, [`09`](09_gold_data_quality_report.md) §Stage 2.)

### B2) Flat-rate v2 vs contract-true v3

**Problem:** The data stages richer contract terms (`sla_target_days` per mode, `sla_penalty_pct_per_day` = 2%/day, `dim_contract_terms` rebate tiers) than the shipped measures use (flat 3% SLA penalty; volume-only 1/3/5% rebate `SWITCH`).

**Decision:** Ship the simpler flat-rate DAX in v2; **stage** the finer columns for a v3 "contract-true" rewrite rather than half-wire them.

**Rationale:** A flat 3% is defensible and legible for an exec demo; a day-accurate penalty join is a measurable v3 increment with the data already in place. Documented as a roadmap item, not a gap.

### B3) Data-grounded thresholds (compute, don't guess)

**Problem:** Conditional-formatting bands and reference lines are easy to invent and wrong.

**Decision:** Compute every threshold from the Gold layer before painting it:

- **CTS target 12%** — portfolio weighted CTS is 4.20%; category range 11–56%. 12% = stretch target near what efficient categories already achieve.
- **Late-rate bands 45% / 60%** — portfolio late rate 54.8%; best mode (Standard) 38%. 45 ≈ best-mode floor, 60 ≈ materially worse than portfolio (>5σ of the 51.9–56.8% monthly band).
- **Retention alert < 65%** — portfolio ≈ 69%; segments span 68.9–69.3%, so a literal "below average" rule would noise-flag everything.
- **Removed an unreachable 30% SLA line** — the monthly late rate never drops below 51.9%, so a 30% line is decoration. Re-anchored to the 45% best-mode baseline.

**Lesson (cost us a rework cycle):** *validate conditional-formatting thresholds against actual data ranges before choosing them.* A first pass picked discount-rate bands (12.5%/20%) the data (8.8–11.1%) could never reach.

### B4) Cohort retention DAX bug — row context wiped

**Problem:** The cohort heat map showed identical counts per row and retention rates of 499–1775%.

**Root cause:** `Cohort Retained Customers (Selected Period)` used `FILTER ( ALL ( DIM_CUSTOMER ), … )` as a `CALCULATE` argument, which **replaced** the visual's cohort-row filter instead of intersecting it.

**Fix (`ebc294a`):** wrap in `KEEPFILTERS`. *Pattern: `FILTER(ALL(table), …)` inside `CALCULATE` discards the visual's grouping — use `KEEPFILTERS` when the measure must respect row context.* (Also in [`02`](02_kpi_glossary.md) C4.)

### B5) Captured-pattern PBIR workflow (never guess Power BI's JSON)

**Problem:** Power BI's report JSON (PBIR) has undocumented serialization shapes; hand-authoring them silently breaks bindings on the next Desktop save.

**Decision:** Author the shape once in Desktop, **capture its serialization**, and reuse it as a template. Captured patterns include:

- **Field parameter on an axis:** a concrete field projection + a sibling `fieldParameters` array — never bind `Parameter_Dimensions[Parameter]` directly (groups by literal labels).
- **What-If metadata:** must be a **column-level `extendedProperty`** (`{"version":0,"kind":1}`), not a table-level annotation, or sliders render but drive nothing.
- **Conditional formatting:** rule-based `Cases` (ComparisonKind 0=eq,1=gt,2=gte,3=lt,4=lte) and gradient `FillRule` (`linearGradient2`) shapes.
- **Constant reference line on a bar chart:** object name `y1AxisReferenceLine` (even for an X-axis line); `xAxisReferenceLine` is schema-valid but never renders.
- **Built-in visualType names aren't the UI label:** a stacked bar is `barChart`, not `stackedBarChart` (which triggers a CustomVisualNotFound hunt).

**Rationale:** Treat the tool's own output as the schema of record. This is why the model is TMDL and the report is PBIR — every change is a reviewable diff.

### B6) Hidden slicer default silently skewed the model

**Problem:** CTS/freight figures were quietly inflated report-wide.

**Root cause:** the Freight Surcharge slicer had a **45% value baked into its saved default filter**, so "actuals" were really actuals + 45% freight everywhere.

**Fix:** reset every scenario slicer to its zero default. *Lesson: a What-If slider must default to 0 so the report reads as actuals until the user moves it — audit saved slicer state, not just the measure.*

### B7) Bridging two facts with no direct FK

**Problem:** `Revenue at Risk` needs Net Sales (in `FACT_SALES`) filtered to orders with a late line (in `FACT_FULFILMENT`), but the facts share no direct relationship.

**Decision:** bridge by **`order_id` set membership** — collect late order IDs from fulfilment, then `CALCULATE([Net Sales], FACT_SALES[order_id] IN LateOrderIDs)`. Retired the v1 `[Net Sales] × [Late Delivery Rate %]` scalar, which double-counted partial lateness. (DAX in [`02`](02_kpi_glossary.md) F1.)

---

## Summary: What This Demonstrates

**Silver (Part A):**

- PII-safe modelling
- auditable parsing and lineage
- standardisation discipline (keys + labels)
- master-data correction pattern (reference-driven fixes)
- platform-aware SQL engineering in Databricks/Delta
- robustness to missing data (zipcode NULLs)
- stable data contracts for downstream modelling

**v2 (Part B):**

- transparent data provenance (benchmark enrichment, labelled, integrity-checked)
- pragmatic scope discipline (flat-rate v2, contract-true v3 staged)
- data-grounded thresholds over guessed ones
- DAX context mastery (the `KEEPFILTERS` cohort fix; fact-to-fact bridging)
- tool-as-schema-of-record discipline (captured PBIR patterns; audited slicer state)
