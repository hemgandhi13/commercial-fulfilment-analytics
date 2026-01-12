# Silver Data Quality Report (Day 2)

## Scope

This report documents the main Silver layer validations across:

- v1: `silver.dataco_supplychain_clean`
- v2: `silver.dataco_supplychain_clean_v2`
- v3: `silver.dataco_supplychain_clean_v3`
- current: `silver.dataco_supplychain_clean_current`

All results below are copied from Databricks SQL outputs.

---

## 1) Row Count Reconciliation

**Expectation:** Silver should not drop rows relative to upstream Bronze audited input, and later Silver iterations should remain row-stable.

**Result**
| v1_rows | v2_rows | v3_rows |
|--------:|--------:|--------:|
| 180,519 | 180,519 | 180,519 |

**Conclusion:** Row counts are stable across all Silver versions.

---

## 2) Timestamp Parsing Nulls (v1)

**Expectation:** near-zero parse failures.

**Result**
| order_ts_nulls | ship_ts_nulls | total_rows |
|--------------:|--------------:|-----------:|
| 0 | 0 | 180,519 |

**Conclusion:** Timestamp parsing is fully successful for this dataset.

---

## 3) Primary Key / Identifier Nulls (v3)

**Expectation:** core identifiers should not be NULL.

**Result**
| null_order_item_id | null_order_id | null_customer_id | null_product_card_id |
|-------------------:|--------------:|-----------------:|----------------------:|
| 0 | 0 | 0 | 0 |

**Conclusion:** All critical identifiers are complete.

---

## 4) Grain Uniqueness (Order Item Grain, v3)

**Expectation:** 1 row per `order_item_id`.

**Result**
| rows | distinct_order_item_id |
|--------:|------------------------:|
| 180,519 | 180,519 |

**Conclusion:** Grain is consistent: 1 row per order item.

---

## 5) Standardisation Impact (v2)

v2 standardises whitespace and key strings. This section demonstrates measurable corrections.

**Result**
| region_corrected_rows | market_corrected_rows | shipmode_corrected_rows | total_rows |
|----------------------:|----------------------:|-------------------------:|-----------:|
| 17,925 | 0 | 0 | 180,519 |

**Interpretation:** The main standardisation gain was `order_region` whitespace cleanup.

Example patterns observed:

- `West of USA␠` → `West of USA`
- `US Center␠` → `US Center`
- `South of␠␠USA␠` → `South of USA`

---

## 6) Encoding Corruption Detection (v2)

Replacement character `�` indicates corrupted encoding in upstream source fields.

**Result**
| bad_country_rows | bad_city_rows | total_rows |
|-----------------:|--------------:|-----------:|
| 37,430 | 15,208 | 180,519 |

**Conclusion:** Significant encoding corruption existed in country/city fields and required controlled remediation.

---

## 7) Controlled Fix Outcomes (v3)

v3 applies reference-driven corrections from `silver.ref_text_fixes`.

**Result**
| bad_order_country_after | bad_order_city_after | bad_customer_country_after | bad_customer_city_after | total_rows |
|------------------------:|---------------------:|----------------------------:|-------------------------:|-----------:|
| 0 | 0 | 0 | 0 | 180,519 |

**Conclusion:** Encoding-corrupted values were fully eliminated in the Silver v3 “clean” columns.

---

## 8) Zipcode Null Rate (Data Property)

High NULL rate in `order_zipcode` is treated as a **source-data property**, not forcibly imputed.

**Result**
| null_order_zip | total_rows |
|--------------:|-----------:|
| 155,679 | 180,519 |

**Decision:** Keep zipcode nullable. Downstream modelling should use NULL-safe key strategies rather than composite joins requiring non-null zipcodes.

---

## 9) Commercial Sanity (v1 Baseline)

**Result**
| min_discount_rate | max_discount_rate | min_net_sales | min_gross_sales | min_profit |
|------------------:|------------------:|--------------:|----------------:|---------------:|
| 0 | 0.25 | 7.489999771 | 9.989999771 | -4274.97998 |

**Interpretation:**

- Discount rates fall in a plausible range (0 to 25%).
- Negative profit exists in the dataset. This is not automatically a data error; it can occur due to returns, promotions, loss-leading strategies, or pricing/discount combinations. It is documented rather than “fixed.”

---

## Summary

- Row counts stable across Silver v1/v2/v3 (`180,519`)
- Timestamp parsing succeeded fully (0 nulls)
- Core identifiers complete (0 nulls)
- Grain is clean: 1 row per `order_item_id`
- v2 delivered measurable standardisation (17,925 region corrections)
- v3 eliminated encoding corruption (all `�` resolved in clean columns)
- Zipcodes are often missing (155,679 nulls); treated as a source property and handled downstream with robust keying patterns
