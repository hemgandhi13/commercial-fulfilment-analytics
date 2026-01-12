# Engineering Notes — Errors, Decisions, and Fix Patterns (Silver)

This document summarises the non-trivial engineering issues encountered while building a production-grade Silver layer, and how they were resolved.

The intent is to demonstrate reproducible problem-solving and “enterprise-safe” decision-making.

---

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

## Summary: What This Demonstrates

- PII-safe modelling
- auditable parsing and lineage
- standardisation discipline (keys + labels)
- master-data correction pattern (reference-driven fixes)
- platform-aware SQL engineering in Databricks/Delta
- robustness to missing data (zipcode NULLs)
- stable data contracts for downstream modelling
