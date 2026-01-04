# Databricks notebook source
import re

source_table = "default.data_co_supply_chain_dataset"
target_table = "bronze.dataco_supplychain_raw"

df = spark.table(source_table)

def clean_name(col: str) -> str:
    col = col.strip().lower()
    col = re.sub(r'[\s\-\/]+', '_', col)      # spaces, hyphens, slashes -> _
    col = re.sub(r'[()]+', '', col)           # remove parentheses
    col = re.sub(r'[^0-9a-zA-Z_]', '', col)   # remove other special chars
    col = re.sub(r'__+', '_', col)            # collapse multiple underscores
    return col

clean_cols = [clean_name(c) for c in df.columns]

# Ensuring uniqueness (in case two columns clean to same name)
seen = {}
final_cols = []
for c in clean_cols:
    if c in seen:
        seen[c] += 1
        final_cols.append(f"{c}_{seen[c]}")
    else:
        seen[c] = 0
        final_cols.append(c)

df_clean = df.toDF(*final_cols)

print("Original column count:", len(df.columns))
print("Cleaned column count :", len(df_clean.columns))

(
    df_clean.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(target_table)
)

display(df_clean.limit(5))
