"""
Silver layer: cleaned, validated, conformed data.

Reads the Bronze Delta table and applies the data-quality rules defined in
config/config.yaml. Rows that fail validation are dropped (and counted, so
the run is auditable) rather than silently kept -- Gold-layer consumers
should be able to trust every row in Silver.

Usage:
    python src/silver/clean_transform.py
"""

import os
import sys

from pyspark.sql import functions as F

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.spark_session import get_spark, resolve_table_path, load_config  # noqa: E402


def clean(df, cfg):
    rules = cfg["pipeline"]
    before = df.count()

    cleaned = (
        df.dropDuplicates(["pickup_datetime", "dropoff_datetime", "pickup_zone", "fare_amount"])
        .filter(F.col("fare_amount") >= rules["min_fare_amount"])
        .filter(F.col("trip_distance") <= rules["max_trip_distance_miles"])
        .filter(F.col("passenger_count").isNotNull())
        .filter(F.col("passenger_count").between(rules["min_passenger_count"], rules["max_passenger_count"]))
        .withColumn("pickup_datetime", F.to_timestamp("pickup_datetime"))
        .withColumn("dropoff_datetime", F.to_timestamp("dropoff_datetime"))
        .withColumn("trip_date", F.to_date("pickup_datetime"))
        .withColumn(
            "trip_duration_minutes",
            (F.col("dropoff_datetime").cast("long") - F.col("pickup_datetime").cast("long")) / 60,
        )
    )

    after = cleaned.count()
    print(f"Silver cleaning: {before:,} rows in -> {after:,} rows out "
          f"({before - after:,} dropped by data-quality rules)")
    return cleaned


def run():
    config = load_config()
    spark = get_spark("silver-transform")

    bronze_path = resolve_table_path(config["tables"]["bronze"])
    silver_path = resolve_table_path(config["tables"]["silver"])

    bronze_df = spark.read.format("delta").load(bronze_path)
    silver_df = clean(bronze_df, config)

    (
        silver_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("trip_date")
        .save(silver_path)
    )
    print(f"Wrote Silver table -> {silver_path}")

    spark.stop()


if __name__ == "__main__":
    run()
