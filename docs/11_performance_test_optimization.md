# Performance Evidence — Power BI (Page 05: Discount Leakage)

## Scope

Page: **05 Discount Leakage Table**  
Primary risk: table/matrix responsiveness under slicers (Market / Category / State / Year).

## Measurement

Tool: **Power BI Desktop → Performance Analyzer**  
Action: **Refresh visuals**  
Proof assets:

- `powerbi/Screenshots/05_performance_before.png`
- `powerbi/Screenshots/05_performance_after.png`

## Optimisation implemented

**Reduce table workload via Top-N constraint on categories by discount dollars.**

Implementation (v1):

- Visual-level filter on the table:
  - Field: `CATEGORY_NAME`
  - Filter type: **Top N**
  - Top: **25**
  - By value: **Discount Amount**

(Alt test also executed: rank-based cap; recorded below.)

## Results (Table visual)

### Test A — Rank cap (≤ 20)

Table (ms): **97**

- DAX query: **17**
- Visual display: **40**
- Other: **40**

### Test B — Top N = 25 by Discount Amount (v1)

Table (ms): **283**

- DAX query: **15**
- Visual display: **164**
- Other: **105**

## Readout (what matters)

- The table is **render-bound**, not DAX-bound (DAX stays ~15–17ms).
- Performance variance is driven by **visual display + overhead** (formatting, cell count, layout work).
- v1 Top-N constraint keeps the page executive-usable while limiting worst-case table explosion.

## Tuning backlog (if pushing <200ms consistently)

Order of impact for this page:

1. Reduce displayed table columns/measures (cuts cell count immediately)
2. Reduce/limit conditional formatting (apply to 1–2 columns max)
3. Disable unnecessary cross-interactions from the table (Edit interactions)
4. Add drillthrough for full detail; keep page 05 as “Top contributors only”
