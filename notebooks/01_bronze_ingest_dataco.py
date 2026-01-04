from pyspark.sql.functions import current_timestamp, lit

source_table = "bronze.dataco_supplychain_raw"
target_table = "bronze.dataco_supplychain_raw_audited"
batch_id = "day1_initial"

df = spark.table(source_table)

df_audit = df.withColumn("_ingest_ts", current_timestamp()).withColumn(
    "_batch_id", lit(batch_id)
)

(
    df_audit.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(target_table)
)

print("Wrote:", target_table)
