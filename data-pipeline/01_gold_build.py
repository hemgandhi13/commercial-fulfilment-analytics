# =============================================================================
# 01_gold_build.py
# Gold layer curation — FACT_SALES and FACT_FULFILMENT
#
# Source:  workspace.silver.dataco_supplychain_clean_current
# Target:  workspace.gold.fact_sales
#          workspace.gold.fact_fulfilment
#
# Design contract
# ---------------
# Power BI reads these tables as CSVs via pDataFolder / fnLoadCsv.
# The M code in FACT_SALES and FACT_FULFILMENT applies:
#   1. Table.PromoteHeaders + Text.Trim      — expects clean, trimmed headers
#   2. Table.TransformColumnNames(Text.Upper) — expects ALL lowercase headers
#   3. KeyText: scientific-notation guard on GEO_KEY, CHANNEL_KEY, ORDER_ZIPCODE
#      via `Number.ToText(Number.RoundDown(…), "0")` — caused by BIGINT xxhash64
#      values serialising to float notation in CSV (e.g. 3.47e+18)
#   4. Table.TransformColumnTypes — full explicit type cast of every column
#
# This script resolves ALL four debt items so Power Query becomes a pass-through:
#   - All column names are lowercase and trimmed (no Text.Trim needed)
#   - xxhash64 surrogate keys are CAST to STRING before export (no sci-notation)
#   - order_zipcode is STRING (no extra cast needed in M)
#   - Delta column types match the TMDL target types exactly (no M casting needed)
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    LongType, DoubleType, StringType, IntegerType, TimestampType
)

spark = SparkSession.builder.getOrCreate()

SILVER = "workspace.silver.dataco_supplychain_clean_current"
GOLD   = "workspace.gold"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {GOLD}")

silver = spark.table(SILVER)


# ---------------------------------------------------------------------------
# Shared surrogate key expressions
# Debt item 3: cast to STRING so CSV serialisation never produces sci-notation
# ---------------------------------------------------------------------------
def geo_key(country_key, state_key, city_key):
    return F.cast(
        F.xxhash64(
            F.coalesce(F.col(country_key), F.lit("")),
            F.coalesce(F.col(state_key),   F.lit("")),
            F.coalesce(F.col(city_key),    F.lit("")),
        ),
        StringType(),
    ).alias("geo_key")


def channel_key(market_key, region_key, mode_key):
    return F.cast(
        F.xxhash64(
            F.coalesce(F.col(market_key), F.lit("")),
            F.coalesce(F.col(region_key), F.lit("")),
            F.coalesce(F.col(mode_key),   F.lit("")),
        ),
        StringType(),
    ).alias("channel_key")


def date_key(date_col):
    return F.cast(F.date_format(F.col(date_col), "yyyyMMdd"), LongType())


# ---------------------------------------------------------------------------
# fact_sales
# TMDL target types (from FACT_SALES.tmdl):
#   int64  : order_item_id, order_id, customer_id, product_card_id,
#             category_id, department_id, order_date_key, discount_band_key,
#             quantity
#   double : gross_sales, net_sales, discount_amount, discount_rate,
#             profit, unit_price
#   string : geo_key, channel_key, order_status, _batch_id
#   datetime: _ingest_ts
# ---------------------------------------------------------------------------
fact_sales = silver.select(
    F.col("order_item_id").cast(LongType()),
    F.col("order_id").cast(LongType()),
    F.col("customer_id").cast(LongType()),
    F.col("product_card_id").cast(LongType()),
    F.col("category_id").cast(LongType()),
    F.col("department_id").cast(LongType()),

    date_key("order_date").alias("order_date_key"),

    geo_key("order_country_key", "order_state_key", "order_city_key"),
    channel_key("market_key", "order_region_key", "shipping_mode_key"),

    F.when(F.col("discount_rate") == 0,                                              F.lit(1))
     .when((F.col("discount_rate") > 0)    & (F.col("discount_rate") <= 0.05),       F.lit(2))
     .when((F.col("discount_rate") > 0.05) & (F.col("discount_rate") <= 0.10),       F.lit(3))
     .when((F.col("discount_rate") > 0.10) & (F.col("discount_rate") <= 0.15),       F.lit(4))
     .when((F.col("discount_rate") > 0.15) & (F.col("discount_rate") <= 0.20),       F.lit(5))
     .when((F.col("discount_rate") > 0.20) & (F.col("discount_rate") <= 0.25),       F.lit(6))
     .otherwise(F.lit(None).cast(LongType()))
     .cast(LongType())
     .alias("discount_band_key"),

    F.col("gross_sales").cast(DoubleType()),
    F.col("net_sales").cast(DoubleType()),
    F.col("discount_amount").cast(DoubleType()),
    F.col("discount_rate").cast(DoubleType()),
    F.col("profit").cast(DoubleType()),
    F.col("quantity").cast(LongType()),
    F.col("unit_price").cast(DoubleType()),

    F.col("order_status").cast(StringType()),

    F.col("_ingest_ts").cast(TimestampType()),
    F.col("_batch_id").cast(StringType()),
)

(
    fact_sales.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{GOLD}.fact_sales")
)

print("✓ fact_sales written")


# ---------------------------------------------------------------------------
# fact_fulfilment
# TMDL target types (from FACT_FULFILMENT.tmdl):
#   int64  : order_item_id, order_id, customer_id, product_card_id,
#             category_id, department_id, order_date_key, ship_date_key,
#             days_for_shipping_real, days_for_shipment_scheduled,
#             shipping_days_variance, late_delivery_risk, is_late_by_days
#   string : geo_key, channel_key, delivery_status, shipping_mode,
#             order_status, order_zipcode, _batch_id
#   datetime: _ingest_ts
#
# Debt item 3b: order_zipcode → STRING (M cast `Text.From(_, "en-US")` removed)
# Debt item (derived measure): shipping_days_variance computed here, not in M
# ---------------------------------------------------------------------------
fact_fulfilment = silver.select(
    F.col("order_item_id").cast(LongType()),
    F.col("order_id").cast(LongType()),
    F.col("customer_id").cast(LongType()),
    F.col("product_card_id").cast(LongType()),
    F.col("category_id").cast(LongType()),
    F.col("department_id").cast(LongType()),

    date_key("order_date").alias("order_date_key"),
    date_key("ship_date").alias("ship_date_key"),

    geo_key("order_country_key", "order_state_key", "order_city_key"),
    channel_key("market_key", "order_region_key", "shipping_mode_key"),

    F.col("days_for_shipping_real").cast(LongType()),
    F.col("days_for_shipment_scheduled").cast(LongType()),
    (F.col("days_for_shipping_real") - F.col("days_for_shipment_scheduled"))
        .cast(LongType())
        .alias("shipping_days_variance"),
    F.col("late_delivery_risk").cast(LongType()),
    F.col("is_late_by_days").cast(LongType()),

    F.col("delivery_status").cast(StringType()),
    F.col("shipping_mode").cast(StringType()),
    F.col("order_status").cast(StringType()),

    # Debt item 3b: explicit STRING cast eliminates M's Text.From() guard
    F.col("order_zipcode").cast(StringType()),

    F.col("_ingest_ts").cast(TimestampType()),
    F.col("_batch_id").cast(StringType()),
)

(
    fact_fulfilment.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{GOLD}.fact_fulfilment")
)

print("✓ fact_fulfilment written")


# ---------------------------------------------------------------------------
# Post-write assertion: verify no BIGINT keys leaked into the output
# (geo_key / channel_key must be StringType in the Delta schema)
# ---------------------------------------------------------------------------
for tbl in ("fact_sales", "fact_fulfilment"):
    schema = spark.table(f"{GOLD}.{tbl}").schema
    for field in schema:
        if field.name in ("geo_key", "channel_key"):
            assert isinstance(field.dataType, StringType), (
                f"SCHEMA CONTRACT VIOLATION: {tbl}.{field.name} is "
                f"{field.dataType}, expected StringType"
            )
print("✓ schema contract assertions passed")
