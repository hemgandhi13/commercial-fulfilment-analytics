# 01 | BI Brief: Commercial Analytics Executive Dashboard

**Project:** DataCo Supply Chain Analytics (Commercial + Fulfilment)  
**Primary Audience:** Exec / Sales Leadership / Commercial Ops / Fulfilment Ops  
**Refresh Cadence:** Daily (Target) / Weekly (Minimum)

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

## 3. Project Scope

- **Temporal Grain:** Weekly + Monthly performance views (with drill-down where possible).
- **Dimensional Slicing:** Product/Category, Region/Geography, Sales Channel, Customer Segment.
- **Data Source:** DataCo structured dataset (CSV) + variable descriptions. Clickstream is out-of-scope for Week 1 (optional later enhancement).
- **Architecture:**
  - **Databricks:** Medallion pipeline (Bronze = raw ingest, Silver = cleaned/standardised, Gold = business-ready dimensional tables).
  - **Snowflake:** Curated serving layer (Gold star schema tables/views).
  - **Power BI Desktop:** Semantic model (relationships + DAX measures) and report experience.

---

## 4. Deliverables

1. **Governed KPI layer:** KPI definitions documented and applied consistently across all report pages.
2. **Star schema model:** Fact + dimension tables (validated grain, keys, and relationships) served from Snowflake.
3. **Executive-ready dashboard:** Minimum 6 pages (Overview, Revenue/Margin, Pricing/Discount, Customer/Cohorts, Ops/OTIF, Data Quality/KPI Definitions).
4. **Ops readiness:** Data quality checks + refresh runbook + at least one documented performance optimisation.
5. **Security:** RLS design documented (implemented where feasible in semantic model).

---

## 5. Success Criteria (Measurable)

To be considered “production-shaped” for portfolio purposes, this project must achieve:

1. **Consistency:** All KPIs defined in `02_kpi_glossary.md` and implemented consistently in Power BI.
2. **Technical Integrity:** Validated star schema built and queryable in Snowflake; model grain is unambiguous.
3. **Decision Coverage:** Dashboard directly answers the 5 decision questions in Section 2 with drill paths.
4. **Operational Discipline:** Includes documented data quality checks, refresh/runbook, and at least one performance optimisation note (what changed + why).

---

## 6. Key Assumptions & Constraints

- The dataset contains sufficient fields for revenue/profit/discount analysis and delivery timeliness metrics.
- “In-Full” may require a proxy if line-item fulfilment quantities are unavailable (OTIF-lite definition will be documented explicitly).
- This is a one-week build; scope is intentionally limited to one flagship dashboard and governance artefacts.

---

## 7. Stakeholder Sign-off (Portfolio Simulation)

| Role                       | Responsibility                                                           |
| :------------------------- | :----------------------------------------------------------------------- |
| **Sales Lead**             | Revenue performance, category/channel interpretation                     |
| **Commercial/Ops Manager** | Fulfilment logic (OTD/OTIF-lite), operational drivers                    |
| **BI Engineer**            | Data modelling, KPI governance, security approach (RLS), refresh/runbook |
