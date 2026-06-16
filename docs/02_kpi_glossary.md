# 02 | KPI Glossary (Commercial + Fulfilment)

**Note:** KPI definitions are the source of truth. The implemented DAX measures (in the semantic model's `_Measures.tmdl`) match these definitions; where a measure is implemented, its **exact name and DAX** are shown so this glossary doubles as the measure dictionary.  
**Status:** Sections **A–D** are the v1 commercial/fulfilment baseline (bound to real Gold columns). Sections **E–G** are the **v2 commercial upgrade** (cost-to-serve, DIFOT financialization, trade-spend rebates, What-If scenarios).

> **Column-name casing:** Gold CSV headers are lowercase (`net_sales`); the semantic model promotes them to UPPERCASE (`FACT_SALES[net_sales]` ↔ display `NET_SALES`). DAX below uses the model form.
>
> **v2 cost provenance:** The cost/freight/SLA/rebate *rates* in Sections E–F are benchmark assumptions encoded in DAX (DataCo carries no such fields). See [`01_bi_brief.md`](01_bi_brief.md) §2A and [`03_data_dictionary_notes.md`](03_data_dictionary_notes.md) §6.

### Measure-folder map (`_Measures.tmdl`)

| Folder | Theme | Glossary section |
| :----- | :---- | :--------------- |
| A. Base Commercial · C. Revenue & Ratios | Sales, profit, AOV, margin | A |
| B. Pricing & Discounts | Discount amount/rate | B |
| D. Time Intelligence | MTD/YTD/LY/YoY/Rolling 12M | A (time variants) |
| E–G. Fulfilment / Severity / Ship-Date | OTD, late rate, lead time | D |
| H. Customer Logic | Distinct/new/returning, cohorts | C |
| **K. Cost-to-Serve** | ABC handling, freight, NCM | **E** |
| **L. Supply Chain Risk & Trade Spend** | Revenue at risk, SLA penalty, rebate, True Net Profit | **F** |
| **L. Scenario Planning** | What-If harvest measures | **G** |
| J. Data Trust | Row counts, FK checks, flags | see [`09`](09_gold_data_quality_report.md) |

---

## A. Revenue & Margin

### KPI A1 — Gross Sales

- **Purpose:** Baseline commercial volume before discount adjustment.
- **Definition:** Total sales value before discount. In this dataset `gross_sales`, `net_sales`, and `discount_amount` are **separate Gold columns** (`gross_sales − discount_amount = net_sales`), so the hedge is resolved: Gross ≠ Net.
- **Implemented as:** `Total Gross Sales = SUM ( FACT_SALES[gross_sales] )`.
- **Grain:** Order-line (`order_item_id`).
- **Notes/Edge Cases:** Used as the denominator for `Discount Rate % (Effective)` (B2).

### KPI A2 — Net Sales

- **Purpose:** Revenue after discount — the spine of the commercial model.
- **Definition:** `net_sales = gross_sales − discount_amount` (verified by the waterfall bridge check in [`09`](09_gold_data_quality_report.md)). The dataset has no explicit returns/cancellations field, so those are not deducted.
- **Implemented as:** `Net Sales = SUM ( FACT_SALES[net_sales] )`.
- **Grain:** Order-line. Net Sales is the denominator for margin, CTS %, AOV, and the entire v2 commercial stack.
- **Notes/Edge Cases:** `order_status` / `delivery_status` labels exist but are **not** used to net out revenue — all lines are treated as realised sales (documented, not silently assumed).

### KPI A3 — Profit / Benefit per Order

- **Purpose:** Profitability outcome used for margin analysis.
- **Definition:** Profit (or “benefit”) attributed to an order/order-line as supplied by dataset or derived from revenue minus cost.
- **Calculation:** `SUM(Profit)` or `SUM(BenefitPerOrder)` (preferred if provided).
- **Grain:** Transaction/order-line.
- **Notes/Edge Cases:** If only per-order profit exists, ensure you do not double-count when joining to dimensions.

### KPI A4 — Gross Margin %

- **Purpose:** Profitability efficiency.
- **Definition:** Profit as a percentage of Net Sales.
- **Calculation:** `Gross Margin % = Profit / Net Sales`
- **Grain:** Aggregated view (report level).
- **Notes/Edge Cases:** Use safe division; if Net Sales = 0, return blank (not 0).

### KPI A5 — Average Order Value (AOV)

- **Purpose:** Basket economics.
- **Definition:** Average Net Sales per distinct order.
- **Calculation:** `AOV = Net Sales / Distinct Orders`
- **Grain:** Aggregated view (time period + slicers).
- **Notes/Edge Cases:** If only order-line grain exists, Distinct Orders must use Order ID distinct count.

---

## B. Pricing / Discount

### KPI B1 — Discount Amount

- **Purpose:** Quantify commercial leakage via discounting.
- **Definition:** Total discount value applied to orders/order-lines.
- **Calculation (choose based on available fields):**
  - Preferred: `SUM(DiscountAmount)` if a dedicated field exists
  - Proxy: `SUM(ListPrice - SellingPrice) * Quantity` if list and selling prices exist
  - Proxy (rate): `Net Sales * Discount Rate` if rate exists but amount does not
- **Grain:** Order-line preferred (most accurate).
- **Notes/Edge Cases:** If multiple discount types exist (promo/coupon), define inclusion rules.

### KPI B2 — Discount Rate %

- **Purpose:** Standardise discount intensity across products/regions/channels.
- **Definition:** Discount Amount as a percentage of Gross Sales (or list value where available).
- **Calculation:** `Discount Rate % = Discount Amount / Gross Sales`
- **Grain:** Aggregated.
- **Notes/Edge Cases:** If Gross Sales not available, use `Discount Amount / Net Sales` and document.

### KPI B3 — Profit After Discount

- **Purpose:** True commercial outcome after discounting.
- **Definition (resolved):** In this dataset `profit` is the **per-line benefit already net of discount**, so `Profit After Discount = Profit` — no further subtraction. `Profit = SUM ( FACT_SALES[profit] )`.
- **Grain:** Order-line. Negative values are valid (loss-making lines exist; see [`06`](06_data_quality_report.md) §9).
- **v2 supersession:** Discount is no longer the *last* deduction. v2 carries Profit forward into **Net Commercial Margin** = `Profit − Total Cost-to-Serve` (Section E) and ultimately **True Net Profit** (Section F). "Profit After Discount" is the v1 bottom line; "True Net Profit (Post-Rebate)" is the v2 bottom line.

---

## C. Customer & Retention (Transactional Retention)

### KPI C1 — Distinct Customers

- **Purpose:** Customer base size for slicing and retention metrics.
- **Definition:** Number of unique customers with at least one qualifying purchase in the selected period.
- **Calculation:** `DISTINCTCOUNT(CustomerID)`
- **Grain:** Period + slicers.
- **Notes/Edge Cases:** Exclude cancelled orders if cancellation status exists (align with Net Sales logic).

### KPI C2 — Repeat Purchase Rate

- **Purpose:** Measure customer stickiness in transaction-based businesses.
- **Definition:** Percentage of customers who made 2+ purchases within the selected window.
- **Calculation (conceptual):**
  - `Repeat Customers = COUNT(customers with Orders >= 2)`
  - `Repeat Purchase Rate = Repeat Customers / Customers with Orders >= 1`
- **Grain:** Period + slicers.
- **Notes/Edge Cases:** Define the window (e.g., last 90 days vs calendar month). For Week 1, use the report filter period.

### KPI C3 — Customer Cohorts (First Purchase Month)

- **Purpose:** Cohort-based retention tracking.
- **Definition:** Assign each customer a cohort based on the month of their first recorded purchase.
- **Calculation:** `CohortMonth = MIN(OrderDate) by Customer`, truncated to month.
- **Grain:** Customer.
- **Notes/Edge Cases:** Ensure first purchase is based on qualifying orders (exclude cancellations if applicable).

### KPI C4 — Retention % by Month (Cohort-style)

- **Purpose:** Show how cohorts retain over subsequent months.
- **Definition:** For each cohort month, the percentage of cohort customers who purchase again in month N.
- **Calculation (conceptual):**
  - `Cohort Size = Distinct Customers in CohortMonth`
  - `Active in Month N = Distinct Customers from cohort with purchase in Month N`
  - `Retention % = Active in Month N / Cohort Size`
- **Implemented as:** `Cohort Retention % (Post-Acquisition)` over `Cohort Retained Customers (Selected Period)`. Cohort month comes from `DIM_CUSTOMER[First Purchase YearMonthSort]` (first qualifying order per customer).
- **Grain:** CohortMonth × ActivityMonth. **Requires a year/period selection** to be meaningful — with no selection, “acquired before period start” is empty by definition.
- **⚠ Known-bug lesson (fixed `ebc294a`):** the retained-customers measure originally used `FILTER ( ALL ( DIM_CUSTOMER ), … )`, which **replaced** the visual's cohort row filter — every cohort row showed the same portfolio count and rates of 499–1775%. Fixed by wrapping in `KEEPFILTERS` so the cohort filter **intersects** rather than replaces the row context. *Pattern: `FILTER(ALL(table), …)` as a `CALCULATE` argument wipes visual row context — wrap in `KEEPFILTERS` when the measure must respect the visual's grouping.*

---

## D. Operations / Fulfilment

> **Resolved lateness definition (read first):** DataCo carries a binary `late_delivery_risk` flag (1 = late), which equals exactly the rows where `delivery_status = 'Late delivery'`: **98,977 of 180,519 = 54.8%** portfolio late rate. All fulfilment measures below key off this flag. A *second, broader* signal — `is_late_by_days ≥ 1` (actual shipping days > scheduled) — covers **103,400 = 57.3%**; the dashboard headline uses the 54.8% flag for consistency. See [`09`](09_gold_data_quality_report.md) for the reconciliation. **In-Full cannot be derived** (no quantity-delivered field), so true OTIF is out of scope and the metric is the On-Time rate, explicitly labelled.

### KPI D1 — Late Delivery Rate % / On-Time Delivery Rate %

- **Purpose:** Delivery timeliness performance (the operational headline).
- **Definition:** Share of fulfilment lines flagged late. `On-Time = 1 − Late`.
- **Implemented as:**
  - `Late Orders (Fulfilment) = CALCULATE ( [Fulfilment Orders], FACT_FULFILMENT[late_delivery_risk] = 1 )`
  - `Late Delivery Rate % = DIVIDE ( [Late Orders (Fulfilment)], [Fulfilment Orders] )`
  - `On-Time Delivery Rate % = 1 − [Late Delivery Rate %]`
  - `Late Delivery Rate % (3M Rolling)` smooths the monthly trend.
- **Grain:** Order-line in `FACT_FULFILMENT`. Reportable by any conformed dimension (market, mode, category…).
- **Data-grounded thresholds (v2):** monthly late rate ranges 51.9–56.8% (σ ≈ 1.0%); by mode Standard ≈ 38%, Same Day ≈ 46%, Second Class ≈ 77%, First Class ≈ 95%. The dashboard uses **45% (best-mode baseline) / 60% (materially worse than portfolio)** as the green/gold/red bands — a literal 30% SLA line is unreachable and was removed as decoration (see [`07`](07_engineering_notes_errors_and_decisions.md) §B).

### KPI D2 — OTIF status (In-Full not derivable)

- **Purpose:** Operational reliability indicator.
- **Decision (resolved):** True OTIF (On-Time **In-Full**) **cannot be computed** — there is no per-line quantity-delivered / fill-rate field. The model therefore reports **On-Time only** (KPI D1) and does not claim OTIF. This is stated on the dashboard rather than proxied silently.
- **v3 candidate:** the v2 enrichment stages `expected_delivery_date` / `actual_delivery_date` columns (benchmark-derived) that could support a date-accurate on-time recomputation; fill-rate would still require source data that does not exist.

### KPI D3 — Shipping Speed & Variance

- **Purpose:** Fulfilment speed and schedule adherence.
- **Implemented as:**
  - `Avg Shipping Days (Real) = AVERAGE ( FACT_FULFILMENT[days_for_shipping_real] )`
  - `Avg Shipping Days (Scheduled) = AVERAGE ( FACT_FULFILMENT[days_for_shipment_scheduled] )`
  - `Avg Shipping Variance` / `Shipping Gap (Days)` = real − scheduled (Gold range **−2 to +4** days).
  - Severity: `Avg Late Days (Late Orders Only)`, `% Orders Late 3+ Days`.
- **Grain:** Order-line. `shipping_days_variance` is precomputed in the Gold build (`01_gold_build.py`), not in DAX.
- **Notes/Edge Cases:** A ship-date role-playing relationship (inactive, activated via `USERELATIONSHIP`) powers `Late Delivery Rate % (Ship Date)` / `Fulfilment Orders (Ship Date)` for ship-date-based cuts.

---

## E. Cost-to-Serve (v2) — folder `K. Cost-to-Serve`

> Activity-based costing (ABC). Rates are FMCG/retail benchmark assumptions encoded in DAX (DataCo has no cost columns). Portfolio CTS ≈ **$1.39M on $33.05M Net Sales = 4.20% weighted** at 0% surcharge; category-level range 11–56% (CDs/Toys are structural outliers).

### KPI E1 — Handling Cost (ABC)

- **Definition:** Order-processing + per-unit pick/pack cost.
- **DAX:** `Handling Cost (ABC) = ( [Orders] * 2.50 ) + ( [Quantity] * 0.50 )` — $2.50 per order + $0.50 per unit.
- **Notes:** Driven by order/unit counts only; **does not** react to the Freight Surcharge slider.

### KPI E2 — Freight Cost (Est)

- **Definition:** Estimated outbound freight, by shipping mode, scaled by the What-If freight surcharge.
- **DAX:**
  ```DAX
  Freight Cost (Est) =
  VAR BaseFreight =
      SUMX (
          FACT_SALES,
          VAR ShipMode = RELATED ( DIM_CHANNEL[SHIPPING_MODE] )
          RETURN SWITCH ( ShipMode,
              "Same Day",     FACT_SALES[QUANTITY] * 8,
              "First Class",  FACT_SALES[QUANTITY] * 5,
              "Second Class", FACT_SALES[QUANTITY] * 3,
              FACT_SALES[QUANTITY] * 1.5 )   -- Standard (default)
      )
  RETURN BaseFreight * ( 1 + [Selected Freight Surcharge %] )
  ```
- **Notes:** Per-unit rates $8 / $5 / $3 / $1.50. The Gold export also carries a finer `base_freight_cost` column ($8.50 / $5 / $3 / $1.75 + 8% fuel surcharge) staged for a v3 "contract-true" rewrite; the **v2 measure uses the DAX SWITCH**, not that column.

### KPI E3 — MOQ Penalty Surcharge

- **Definition:** $25 LTL (less-than-truckload) penalty on lines below the What-If minimum-order quantity.
- **DAX:** `SUMX ( FACT_SALES, IF ( FACT_SALES[QUANTITY] < [Selected MOQ Threshold] && [Selected MOQ Threshold] > 0, 25, 0 ) )`.
- **Notes:** $0 when the MOQ slider is at 0 (default). Feeds Total Cost-to-Serve.

### KPI E4 — Total Cost-to-Serve

- **DAX:** `Total Cost-to-Serve = [Handling Cost (ABC)] + [Freight Cost (Est)] + [MOQ Penalty Surcharge]`.
- **Companion:** `CTS % of Net Sales = DIVIDE ( [Total Cost-to-Serve], [Net Sales] )`. Conditional band: red > 12%, gold 9–12%, ink < 9%.

### KPI E5 — Net Commercial Margin (NCM)

- **Purpose:** The v2 margin headline — profit *after the cost of serving the sale*.
- **DAX:** `Net Commercial Margin = [Profit] − [Total Cost-to-Serve]`; `Net Commercial Margin % = DIVIDE ( [Net Commercial Margin], [Net Sales] )`.
- **Notes:** Where v1 stopped at Gross Margin %, v2 surfaces NCM beside it so the CTS erosion is visible per category/department/mode.

---

## F. Supply Chain Risk & Trade Spend (v2) — folder `L`

> DIFOT financialization (put a dollar value on late delivery) + tiered retailer rebates. The 3% SLA penalty and 1/3/5% rebate tiers are benchmark assumptions.

### KPI F1 — Revenue at Risk (Late SLA)

- **Definition:** Net Sales on orders that have **any** late-flagged fulfilment line. The two facts share no direct FK, so lateness is bridged by `order_id` set membership.
- **DAX:**
  ```DAX
  Revenue at Risk (Late SLA) =
  VAR LateOrderIDs =
      CALCULATETABLE ( VALUES ( FACT_FULFILMENT[order_id] ),
                       FACT_FULFILMENT[late_delivery_risk] = 1 )
  RETURN CALCULATE ( [Net Sales], FACT_SALES[order_id] IN LateOrderIDs )
  ```
- **Notes:** Replaces the **retired** v1 `Revenue at Risk` (folder I, `[Net Sales] * [Late Delivery Rate %]`) — a flat scalar that double-counted partial lateness. No visual binds the legacy measure (verified report-wide).

### KPI F2 — Estimated SLA Penalty

- **DAX:** `Estimated SLA Penalty = [Revenue at Risk (Late SLA)] * 0.03` (flat 3% contractual penalty).
- **v3 candidate:** the data stages `sla_target_days` (1/3/5/7 by mode) and `sla_penalty_pct_per_day` (2%/day, 24h grace) for a day-accurate penalty on contract-breach rows; v2 uses the flat 3%.

### KPI F3 — Retailer Rebate Accrual

- **Definition:** Volume-tiered retrospective rebate, shiftable by the What-If rebate slider.
- **DAX:**
  ```DAX
  Base Retailer Rebate Accrual =
  SWITCH ( TRUE (),
      [Net Sales] > 5000000, [Net Sales] * 0.05,
      [Net Sales] > 1000000, [Net Sales] * 0.03,
      [Net Sales] * 0.01 )

  Retailer Rebate Accrual =
  [Base Retailer Rebate Accrual] + ( [Net Sales] * [Selected Rebate Shift %] )
  ```
- **Notes:** Tiers 5% > $5M, 3% > $1M, else 1%. The `dim_contract_terms` table (segment × Bronze/Silver/Gold tiers) stages a customer-segment-aware rebate for v3; v2 uses the simpler volume `SWITCH`.

### KPI F4 — True Net Profit (Post-Rebate)

- **Purpose:** The v2 bottom line.
- **DAX:** `True Net Profit (Post-Rebate) = [Net Commercial Margin] − [Estimated SLA Penalty] − [Retailer Rebate Accrual]`.
- **Companion (page 01 waterfall):** `Margin Waterfall Step` (folder M) bridges Net Sales → −CTS → −SLA Penalty → −Rebate → True Net Profit.

---

## G. What-If Scenario Parameters & Field Parameters (v2)

> Calculated parameter tables + harvest measures. Each harvest measure defaults to 0 so reports read as *actuals* until a slider is moved.

| Parameter table | Range / step | Harvest measure | Wired into |
| :-------------- | :----------- | :-------------- | :--------- |
| `Scenario_FreightSurcharge[Value]` | 0%–50% / 5% | `Selected Freight Surcharge %` = `SELECTEDVALUE(…, 0)` | Freight Cost (Est) → CTS → NCM → True Net Profit |
| `Scenario_MOQ[MOQ_Threshold]` | 0–100 / 5 units | `Selected MOQ Threshold` = `SELECTEDVALUE(…, 0)` | MOQ Penalty Surcharge → CTS |
| `Scenario_Rebate[Rebate_Shift_Pct]` | 0%–5% / 0.5% | `Selected Rebate Shift %` = `SELECTEDVALUE(…, 0)` | Retailer Rebate Accrual → True Net Profit |

- **Cascade:** Dragging Freight Surcharge to 25% moves CTS, NCM %, and True Net Profit live on every page that surfaces them.
- **Field parameter — `Parameter_Dimensions`:** a swappable axis with 4 fields — Product Category (`DIM_CATEGORY[CATEGORY_NAME]`), Product Department (`DIM_DEPARTMENT[DEPARTMENT_NAME]`), Shipping Mode (`DIM_CHANNEL[SHIPPING_MODE]`), Market Region (`DIM_CHANNEL[ORDER_REGION]`). Pages 02–05/07 use a "View By" slicer to re-pivot charts without page bloat (default = Product Category).

> **Gotcha (captured during the build):** What-If metadata must be a **column-level `extendedProperty`** (`{"version":0,"kind":1}` for numeric), not a table-level annotation, or sliders render but drive nothing. Field-parameter bindings hold a concrete field plus a sibling `fieldParameters` array — never bind `Parameter_Dimensions[Parameter]` directly as a projection. See [`07`](07_engineering_notes_errors_and_decisions.md) §B.

---
