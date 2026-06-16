# 04 | Ingestion Log

## Dataset

- Source file: DataCoSupplyChainDataset.csv
- Storage: Databricks managed Delta table
- Target table: bronze.dataco_supplychain_raw
- Medallion layer: Bronze (raw landing)

## Run Metadata

- Batch ID: day1_initial
- Loaded on: 2026-01-02
- Databricks edition: Free Edition
- Validation:
  - row_count: 180519
  - column_count: 53

## Notes

- Column names standardised to snake_case (no spaces/special characters).
- No business logic transformations applied in Bronze.
- Next step: Silver cleaning rules + PII handling + type standardisation.

## v2 note

The Bronze → Silver → Gold **core ingest is unchanged in v2** — same 180,519-row source, same 53 raw columns. The v2 commercial upgrade adds attributes **downstream**, at a second Gold-export stage (`data-pipeline/02_gold_schema_remediation.py`), not at ingest. No new raw source was introduced. See [`03_data_dictionary_notes.md`](03_data_dictionary_notes.md) §6.
