# 01 | BI Brief: Commercial Analytics Executive Dashboard

**Project:** DataCo Supply Chain Analytics (Commercial + Fulfilment)  
**Primary Audience:** Exec / Sales Leadership / Commercial Ops / Fulfilment Ops  
**Refresh Cadence:** Daily (Target) / Weekly (Minimum)  
**Current release:** `v2.0` — commercial decision tool (cost-to-serve, DIFOT financialization, trade-spend rebates, What-If planning)  
**Baseline:** `v1.0` — operational tracker (sales, discounts, late delivery, retention)

> **Document status:** Authored as the v1 charter, updated for v2. Sections 1–2 (problem / decisions) carry forward unchanged; **Section 2A** records the v2 scope expansion, and Sections 3–4 are updated to the delivered v2 state. The full v1→v2 delta lives in the root [`README.md`](../README.md); every measure is defined in [`02_kpi_glossary.md`](02_kpi_glossary.md).

---

## 1. Problem Statement & Business Value

This dashboard consolidates fragmented commercial and fulfilment reporting into a governed analytics layer (single source of truth for this dataset). It enables faster, more reliable decisions by standardising KPI definitions, enforcing consistent slicing (product/region/channel/customer), and surfacing performance drivers across revenue, profitability, discounting, customer behaviour, and delivery execution.

**Business value:**

- Reduce decision latency by replacing manual/fragmented reporting with a consistent KPI layer.
- Identify margin leakage driven by discounting and product mix.
- Detect fulfilment delays and operational bottlenecks (OTIF / lead time).
- Monitor retention signals to prioritise high-value customers at risk.

---

## 2. Key Business Decisions Supported

This dashboard is designed to answer:

- **Product Strategy:** Which product categories are driving revenue vs. margin?
- **Profitability:** Where are aggressive discounts eroding profit?
- **Market Performance:** Which regions or channels are underperforming against baselines?
- **Fulfilment Efficiency:** What is OTIF (On-Time In-Full / OTIF-lite if “in-full” cannot be derived) and where are delays concentrated?
- **Customer Retention:** Which customers are high-value but at risk due to declining purchase frequency?

---

## 2A. v2 Scope Expansion (Descriptive → Prescriptive)

v1 *described* operations ("what shipped, what % was late, how much discount was given"). v2 *prices* them — every operational metric is translated into a dollar impact on net profit, which is the difference between a tracker and a commercial decision tool. The upgrade is organised around four pillars (each maps to specific measures in [`02_kpi_glossary.md`](02_kpi_glossary.md) and pages in the report):

| Pillar | Question it answers | Headline measures |
| :----- | :------------------ | :---------------- |
| **P1. Cost-to-Serve economics** | What does it actually cost to serve this customer/category? | `Total Cost-to-Serve`, `Net Commercial Margin`, `CTS % of Net Sales` |
| **P2. DIFOT financialization** | What is late delivery costing us in dollars? | `Revenue at Risk (Late SLA)`, `Estimated SLA Penalty` |
| **P3. Trade spend & rebates** | What is our true profit after retailer rebates? | `Retailer Rebate Accrual`, `True Net Profit (Post-Rebate)` |
| **P4. What-If scenario planning** | What happens to profit if freight rises 25% / MOQ shifts / rebates change? | `Scenario_FreightSurcharge`, `Scenario_MOQ`, `Scenario_Rebate` + field parameters |

**Net effect on the measure stack:**

```
Net Sales
  − Total Cost-to-Serve        (ABC handling + per-mode freight + MOQ penalty)
  = Net Commercial Margin
  − Estimated SLA Penalty       (3% × Revenue at Risk on late-flagged orders)
  − Retailer Rebate Accrual     (tiered 1/3/5% by net-sales volume + Rebate Shift)
  = True Net Profit (Post-Rebate)
```

The three What-If sliders feed the underlined inputs, so dragging Freight Surcharge to 25% moves CTS, Net Commercial Margin, and True Net Profit live across every page.

> **Data provenance (honest disclosure):** DataCo ships commercial and fulfilment facts but **no** cost-to-serve, freight, SLA-contract, or rebate-tier attributes. v2 introduces those as an explicit, deterministic enrichment layer modelled on FMCG/retail industry benchmarks (see [`03_data_dictionary_notes.md`](03_data_dictionary_notes.md) §6). They are clearly labelled as synthesized throughout — the analytical *methods* (ABC costing, DIFOT financialization, tiered rebates, scenario planning) are production-grade; the *cost rates* are benchmark stand-ins until actuals are available.

---

## 3. Project Scope

- **Temporal Grain:** Weekly + Monthly performance views (with drill-down where possible).
- **Dimensional Slicing:** Product/Category, Department, Region/Geography, Sales Channel/Shipping Mode, Market, Customer Segment.
- **Data Source:** DataCo structured dataset (CSV) + variable descriptions, plus the v2 commercial enrichment layer (benchmark-modelled — see Section 2A disclosure). Clickstream remains out-of-scope.
- **Architecture:**
  - **Databricks:** Medallion pipeline (Bronze = raw ingest, Silver = cleaned/standardised, Gold = business-ready dimensional tables). PySpark is the authoritative transform layer (`data-pipeline/01_gold_build.py`); the v2 commercial enrichment runs as a second Gold stage (`data-pipeline/02_gold_schema_remediation.py`).
  - **Serving layer:** Snowflake served the Gold layer during its trial window; the **Gold CSV export** (`data/databricks_gold_export/`) is the durable, version-controlled serving layer carried by the repo and consumed by Power BI.
  - **Power BI Desktop:** PBIP project — TMDL semantic model (relationships + 60+ DAX measures + RLS + What-If parameters) and a 9-page PBIR report, all version-controlled as text.

---

## 4. Deliverables

1. **Governed KPI layer:** Every KPI defined in [`02_kpi_glossary.md`](02_kpi_glossary.md) and implemented consistently across all report pages — now including the v2 cost-to-serve, DIFOT, and trade-spend families.
2. **Star schema model:** 2 facts + conformed dimensions (validated grain, keys, relationships), served from the Gold CSV export. Contract: [`08_star_schema.md`](08_star_schema.md).
3. **Executive-ready dashboard:** **9 pages** — 01 Executive Overview, 02 Revenue & Margin, 03 Profitability Diagnostic (CTS), 04 Pricing & Discount Impact, 05 Discount Leakage, 06 Operations Overview (DIFOT), 07 Operations Deep Dive, 08 Customer Retention, 09 Data Trust & KPI Definitions.
4. **Commercial decision tooling (v2):** Activity-based Cost-to-Serve, financialized delivery risk, tiered rebate accrual, and three live What-If scenario sliders with swappable field-parameter axes.
5. **Ops readiness:** Data quality checks ([`06`](06_data_quality_report.md)/[`09`](09_gold_data_quality_report.md)) + refresh runbook ([`runboooks/snowflake_load.md`](runboooks/snowflake_load.md)) + documented performance evidence ([`11`](11_performance_test_optimization.md), v1 Performance Analyzer + v2 DAX Studio stress test).
6. **Security:** RLS design documented and verified zero-leakage in the semantic model ([`10_rls.md`](10_rls.md)).

---

## 5. Success Criteria (Measurable)

To be considered “production-shaped” for portfolio purposes, this project must achieve:

1. **Consistency:** All KPIs defined in `02_kpi_glossary.md` and implemented consistently in Power BI.
2. **Technical Integrity:** Validated star schema (queryable in Snowflake during trial; durably served from the Gold CSV export); model grain is unambiguous (1 row per `order_item_id`).
3. **Decision Coverage:** Dashboard directly answers the 5 decision questions in Section 2 with drill paths — and, in v2, prices each in dollars (Section 2A).
4. **Operational Discipline:** Includes documented data quality checks, refresh/runbook, and performance evidence (what changed + why).
5. **Commercial Depth (v2):** Cost-to-serve, revenue-at-risk, rebate, and What-If measures implemented and demonstrably cascading through True Net Profit.

---

## 6. Key Assumptions & Constraints

- The dataset contains sufficient fields for revenue/profit/discount analysis and delivery timeliness metrics.
- **”In-Full” cannot be derived** — DataCo carries no per-line quantity-delivered/fill-rate field — so on-time/late metrics use the `late_delivery_risk` flag (see [`09`](09_gold_data_quality_report.md) for the precise definition). True OTIF is out of scope; this is documented explicitly rather than proxied silently.
- **Cost-to-serve, freight, SLA-contract, and rebate attributes are not in the source.** v2 supplies them as a transparent, deterministic benchmark-modelled enrichment layer (Section 2A disclosure; [`03`](03_data_dictionary_notes.md) §6). The DAX cost/penalty/rebate *rates* are assumptions; the *modelling approach* is production-shaped.
- v1 was a one-week flagship build; **v2 extended it** into a multi-phase commercial upgrade (governance, upstream ETL hardening, advanced semantic modelling, declarative UI, QA/performance) — see the phase log referenced in the README.

---

## 7. Stakeholder Sign-off (Portfolio Simulation)

| Role                       | Responsibility                                                           |
| :------------------------- | :----------------------------------------------------------------------- |
| **Sales Lead**             | Revenue performance, category/channel interpretation                     |
| **Commercial/Ops Manager** | Fulfilment logic (OTD/OTIF-lite), operational drivers                    |
| **BI Engineer**            | Data modelling, KPI governance, security approach (RLS), refresh/runbook |
