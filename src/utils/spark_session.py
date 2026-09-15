"""
Central place to build a SparkSession configured for Delta Lake.

Two storage backends are supported via config/config.yaml -> storage.mode:
  - "local": tables are written to a local Delta Lake under ./data/lake
  - "azure": tables are written to Azure Data Lake Storage Gen2 (ADLS Gen2)
             using the abfss:// protocol. Requires AZURE_STORAGE_ACCOUNT and
             AZURE_STORAGE_KEY to be set as environment variables (or wired
             through a secret scope when running on Databricks).

Keeping this in one place means the ingestion/bronze/silver/gold scripts
don't need to know anything about the underlying storage -- they just ask
for a table path via `resolve_table_path(...)`.
"""

import os
import yaml
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config", "config.yaml")


def load_config(path: str = CONFIG_PATH) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def get_spark(app_name: str = "lakehouse-pipeline") -> SparkSession:
    """Build a SparkSession with Delta Lake support enabled.

    Uses delta-spark's `configure_spark_with_delta_pip` helper, which wires
    up the correct Delta JAR coordinates for the installed pyspark/delta-spark
    version pair and lets Spark fetch them via Maven/Ivy on first run (cached
    locally afterwards). This is the officially recommended way to bootstrap
    Delta from a plain `pip install` environment -- see
    https://docs.delta.io/latest/quick-start.html
    """
    builder = (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        # keeps local runs light -- override via spark-submit/Databricks cluster config in prod
        .config("spark.sql.shuffle.partitions", "4")
    )

    config = load_config()
    if config["storage"]["mode"] == "azure":
        account = os.environ.get("AZURE_STORAGE_ACCOUNT", config["storage"]["azure"]["account_name"])
        key = os.environ.get("AZURE_STORAGE_KEY")
        if key:
            builder = builder.config(
                f"fs.azure.account.key.{account}.dfs.core.windows.net", key
            )

    return configure_spark_with_delta_pip(builder).getOrCreate()


def resolve_table_path(table_name: str) -> str:
    """Return the full storage path for a given logical table name."""
    config = load_config()
    mode = config["storage"]["mode"]

    if mode == "local":
        base = config["storage"]["local"]["base_path"]
        return os.path.join(base, table_name)

    if mode == "azure":
        az = config["storage"]["azure"]
        account = os.environ.get("AZURE_STORAGE_ACCOUNT", az["account_name"])
        container = az["container"]
        return f"abfss://{container}@{account}.dfs.core.windows.net/{table_name}"

    raise ValueError(f"Unknown storage mode: {mode}")
