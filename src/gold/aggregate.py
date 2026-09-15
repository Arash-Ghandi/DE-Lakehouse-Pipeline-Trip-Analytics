"""
Gold layer: business-ready aggregates for BI / dashboards.

Reads Silver and produces a daily revenue-by-zone summary table. Gold
tables are what analysts and dashboards query directly -- they should
never need to touch Bronze or Silver.

Usage:
    python src/gold/aggregate.py
"""

import os
import sys

from pyspark.sql import functions as F

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.spark_session import get_spark, resolve_table_path, load_config  # noqa: E402


def run():
    config = load_config()
    spark = get_spark("gold-aggregation")

    silver_path = resolve_table_path(config["tables"]["silver"])
    gold_path = resolve_table_path(config["tables"]["gold_daily_zone_revenue"])

    silver_df = spark.read.format("delta").load(silver_path)

    gold_df = (
        silver_df.groupBy("trip_date", "pickup_zone")
        .agg(
            F.count("*").alias("trip_count"),
            F.round(F.sum("fare_amount"), 2).alias("total_fare_revenue"),
            F.round(F.sum("tip_amount"), 2).alias("total_tips"),
            F.round(F.avg("trip_duration_minutes"), 1).alias("avg_trip_duration_minutes"),
            F.round(F.avg("trip_distance"), 2).alias("avg_trip_distance_miles"),
        )
        .orderBy("trip_date", "pickup_zone")
    )

    (
        gold_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .save(gold_path)
    )
    print(f"Wrote Gold table -> {gold_path}")

    # also drop a flat CSV export for BI tools / dashboards that don't speak Delta
    export_path = os.path.join(os.path.dirname(gold_path), "exports", "daily_zone_revenue.csv")
    os.makedirs(os.path.dirname(export_path), exist_ok=True)
    gold_df.toPandas().to_csv(export_path, index=False)
    print(f"Exported flat CSV -> {export_path}")

    spark.stop()


if __name__ == "__main__":
    run()
