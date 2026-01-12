# Silver Layer Story

## Objective

Build an enterprise-safe **Silver** table that is:

- **Typed** (explicit data types for IDs, dates, measures)
- **Standardised** (whitespace + canonical key strings for consistent joins)
- **PII-safe** (sensitive customer fields excluded)
- **Data-quality validated**
- A stable upstream for the **Gold star schema** (Power BI + Snowflake replication later)

This repo tracks the evolution of the Silver layer across three iterations (v1 → v2 → v3), ending in a stable “current” object used by downstream models.

---

## Inputs and Lineage

**Primary input (Bronze audited):**

- `workspace.bronze.dataco_supplychain_raw_audited`

Audit lineage preserved:

- `_ingest_ts`
- `_batch_id`

---

## Silver v1 — `silver.dataco_supplychain_clean`

### Why v1 existed

v1 established the baseline Silver contract:

- enforced types
- parsed timestamps and derived `order_date` / `ship_date`
- created explicit commercial measures (`gross_sales`, `net_sales`, `discount_amount`, `discount_rate`, `profit`)
- removed PII
- kept operational fields needed for fulfilment analytics

### PII handling (explicit)

The following fields were intentionally excluded from Silver and all downstream layers:

- `customer_email`
- `customer_password`
- `customer_street`
- `customer_fname`, `customer_lname`

### Date parsing strategy

Source timestamps were strings with inconsistent formats. The pipeline attempts both:

- `M/d/yyyy H:mm`
- `MM/dd/yyyy HH:mm`

and stores:

- raw strings: `order_ts_raw`, `ship_ts_raw`
- parsed timestamps: `order_ts`, `ship_ts`
- derived dates: `order_date`, `ship_date`

---

## Silver v2 — `silver.dataco_supplychain_clean_v2`

### Why v2 was needed

v1 produced correct types and dates, but downstream dimensional modelling requires **consistent join keys** and display strings.
v2 introduced:

1. **Whitespace standardisation**: `trim()` + collapse multiple spaces to one
2. **Canonical key strings**: `UPPER()` + remove punctuation + collapse spaces

This was applied to:

- Geo fields (`order_country/state/city/zipcode`, `customer_country/state/city/zipcode`)
- Channel/ops fields (`market`, `order_region`, `shipping_mode`)
- Plus a controlled standardisation of “USA” variants (e.g., `EE.UU.`, `Estados Unidos`, etc.) into `USA`

### What v2 did _not_ solve

v2 surfaced an important upstream issue:

- the replacement character `�` appeared in country and city fields (encoding corruption)
  This blocks clean dimension labels and creates join fragmentation unless corrected.

---

## Silver v3 — `silver.dataco_supplychain_clean_v3`

### Why v3 was needed

The dataset contains non-recoverable encoding corruption (`�`). This is not a trimming/formatting problem; it is a source-data quality problem.

Instead of attempting unsafe automatic repairs, v3 implements a controlled, auditable approach:

**Pattern: Reference-driven fixes**

- A mapping table `silver.ref_text_fixes` stores corrections for known bad values.
- v3 applies these mappings to produce **clean display columns** and **clean join keys**.

### Key artefacts

**Mapping table:**

- `workspace.silver.ref_text_fixes(field, bad_value, good_value)`
  - `field` is `country` or `city`
  - mappings can be updated safely without rewriting upstream Bronze

**v3 outputs (added columns):**

- Clean display:
  - `order_country_clean`, `order_city_clean`
  - `customer_country_clean`, `customer_city_clean`
- Clean keys:
  - `order_country_clean_key`, `order_city_clean_key`
  - `customer_country_clean_key`, `customer_city_clean_key`

v3 is the final Silver dataset used for all Gold modelling.

---

## Silver “current” — `silver.dataco_supplychain_clean_current`

Downstream tables should never depend on a versioned Silver table name directly.

To provide a stable contract, we expose:

- `workspace.silver.dataco_supplychain_clean_current` (VIEW)

This points to the current best-version Silver implementation (currently v3). When Silver evolves (v4, v5), only the view needs updating, not every downstream table.

---

## Silver Deliverables Summary

### Tables/views

- `silver.dataco_supplychain_clean` (v1 typed + parsed + PII safe)
- `silver.dataco_supplychain_clean_v2` (v2 standardised + canonical keys)
- `silver.dataco_supplychain_clean_v3` (v3 mapped clean labels + clean keys)
- `silver.dataco_supplychain_clean_current` (stable view for downstream)

### Validation approach

Each iteration includes:

- row-count reconciliation
- grain uniqueness checks (`order_item_id`)
- null checks on primary IDs
- timestamp parse null checks (v1)
- corruption checks for `�` (v2/v3)
- documented anomalies and decisions

See: `docs/06_silver_data_quality_report.md`
