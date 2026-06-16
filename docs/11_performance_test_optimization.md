# Performance Evidence — Power BI

Two pieces of evidence:

- **Part 1 (v1):** Performance Analyzer optimisation on Page 05 (Discount Leakage table) — render-bound, fixed with a Top-N constraint.
- **Part 2 (v2):** DAX Studio stress test on the heaviest new commercial measures (`Total Cost-to-Serve`, `True Net Profit`) — confirms the `SUMX`-based CTS model stays well under budget.

---

## Part 1 (v1) — Page 05 Discount Leakage

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

---

## Part 2 (v2) — DAX Studio stress test (commercial measures)

### Scope

The v2 cost-to-serve stack is built on row-by-row `SUMX` iterators (`Freight Cost (Est)`, `MOQ Penalty Surcharge`) feeding `Total Cost-to-Serve` and `True Net Profit (Post-Rebate)`. The risk is that per-row iteration over 180,519 lines, recomputed live under the What-If sliders, becomes the bottleneck. This test measures the heaviest path directly at the engine level.

### Measurement

- **Tool:** DAX Studio (Server Timings).
- **Query:** `SUMMARIZECOLUMNS` with heavy iteration over `[Total Cost-to-Serve]` and `[True Net Profit (Post-Rebate)]`.
- **Budget:** 300 ms total (the “danger threshold” for interactive feel).

### Results

| Metric | Value |
| :----- | ----: |
| **Total time** | **164 ms** |
| Formula Engine (FE) | 94 ms (57.3%) |
| Storage Engine (SE) | 70 ms (42.7%) |

### Readout (what matters)

- **164 ms is well under the 300 ms budget** — no DAX rewrite needed. The `SUMX` CTS model scales fine at this data volume.
- FE-leaning split (57%) is expected for iterator-heavy measures; SE work stays modest because the facts are narrow and keys are clean (string surrogate keys from the Gold build — see [`03`](03_data_dictionary_notes.md)).
- The What-If sliders multiply a single harvested scalar into the iterator (`× (1 + [Selected Freight Surcharge %])`), so dragging a slider does **not** add iteration passes — the live cascade is cheap.

### Verified alongside

- **RLS zero-leakage** (View-as `MarketManager` / `europe_mgr@company.com`) — [`10_rls.md`](10_rls.md).
- **Data trust** — Page 09 confirms 180,519 rows and 0 missing FK keys; the QA evidence block on that page quotes this 164 ms result.
