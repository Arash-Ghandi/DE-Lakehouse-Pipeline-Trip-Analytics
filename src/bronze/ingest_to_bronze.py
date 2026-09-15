"""
Bronze layer: raw ingestion, no business logic.

Reads every CSV under data/raw/, tags each row with ingestion metadata
(source file, ingestion timestamp), and appends it to the Bronze Delta
table. Bronze is intentionally "dumb" -- we never drop or transform data
here, so it always reflects exactly what the source system sent us and
can be replayed if a downstream bug is found.

Usage:
    python src/bronze/ingest_to_bronze.py
"""

import os
import sys

from pyspark.sql import functions as F

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.spark_session import get_spark, resolve_table_path, load_config  # noqa: E402


def run():
    config = load_config()
    spark = get_spark("bronze-ingestion")

    raw_path = config["raw_data"]["path"]
    bronze_path = resolve_table_path(config["tables"]["bronze"])

    csv_files = [f for f in os.listdir(raw_path) if f.endswith(".csv")]
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {raw_path}. "
            "Run src/ingestion/generate_sample_data.py first."
        )

    for filename in csv_files:
        full_path = os.path.join(raw_path, filename)
        df = (
            spark.read.option("header", True)
            .option("inferSchema", True)
            .csv(full_path)
            .withColumn("_source_file", F.lit(filename))
            .withColumn("_ingested_at", F.current_timestamp())
        )

        (
            df.write.format("delta")
            .mode("append")
            .option("mergeSchema", "true")
            .save(bronze_path)
        )
        print(f"Ingested {df.count():,} rows from {filename} -> {bronze_path}")

    spark.stop()


if __name__ == "__main__":
    run()
