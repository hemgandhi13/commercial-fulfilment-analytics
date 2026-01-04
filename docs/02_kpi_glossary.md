# 02 | KPI Glossary (Commercial + Fulfilment)

**Note:** KPI definitions below are the source of truth. Implementation (DAX/SQL) must match these definitions exactly.  
**Binding to dataset columns:** Column mapping will be confirmed during modelling (Day 2).

---

## A. Revenue & Margin

### KPI A1 — Gross Sales

- **Purpose:** Baseline commercial volume before adjustments.
- **Definition:** Total sales value before returns/cancellations and before discount adjustments (if discount is recorded separately).
- **Calculation:** `SUM(SalesAmount)` (or equivalent sales value field).
- **Grain:** Transaction/order-line (depends on source grain).
- **Notes/Edge Cases:** If dataset only provides final paid amount, Gross Sales may equal Net Sales; document that explicitly.

### KPI A2 — Net Sales

- **Purpose:** Revenue after accounting for discounts/returns/cancellations (as supported by data).
- **Definition:** Sales value after excluding cancelled/returned orders and applying discounts where applicable.
- **Calculation (generic):**
  - If returns/cancellations exist: `Gross Sales - Returns - Cancellations`
  - If discount is separate: `Gross Sales - Discount Amount`
- **Grain:** Transaction/order-line.
- **Notes/Edge Cases:** If the dataset lacks explicit returns/cancellations, Net Sales = Gross Sales (document).

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
- **Definition:** Profit measure that reflects discount impact (either already baked into profit field or derived).
- **Calculation (generic):**
  - If Profit already reflects discount: `Profit After Discount = Profit`
  - If Profit is pre-discount and discount is separate: `Profit After Discount = Profit - Discount Amount`
- **Grain:** Transaction/order-line.
- **Notes/Edge Cases:** Must align with how dataset defines profit/benefit.

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
- **Grain:** CohortMonth × ActivityMonth.
- **Notes/Edge Cases:** Use consistent month bucketing; document whether “purchase” includes low-value orders or only qualifying orders.

---

## D. Operations / Fulfilment

### KPI D1 — On-Time Delivery Rate (OTD)

- **Purpose:** Delivery timeliness performance.
- **Definition:** % of delivered orders delivered on or before promised/estimated delivery date (or scheduled delivery metric).
- **Calculation:**
  - `On-Time Delivered Orders / Delivered Orders`
- **Grain:** Order or shipment (depends on fields).
- **Notes/Edge Cases:** Requires an “actual delivery date” and an “expected/promised date” (or scheduled delivery days). If only shipping days exist, use the best available proxy and document.

### KPI D2 — OTIF % (On-Time In-Full) / OTIF-lite

- **Purpose:** Operational reliability indicator.
- **Definition (true OTIF):** Delivered on time AND complete (all items/qty delivered).
- **OTIF-lite definition (if “in-full” cannot be derived):** Delivered on time AND not cancelled/returned (or delivered status indicates completion).
- **Calculation (conceptual):**
  - `OTIF = Orders meeting On-Time AND In-Full criteria / Eligible Orders`
- **Grain:** Order/shipment.
- **Notes/Edge Cases:** If the dataset lacks fill-rate/quantity-delivered fields, we must explicitly label it OTIF-lite in the dashboard.

### KPI D3 — Avg Delivery Lead Time

- **Purpose:** Fulfilment speed.
- **Definition:** Average elapsed time from order date to delivery date (in days).
- **Calculation:** `AVG(DeliveryDate - OrderDate)`
- **Grain:** Order/shipment.
- **Notes/Edge Cases:** Exclude records with missing dates; if only shipping days exist, compute lead time using available day metrics and document.

---
