"""
Unit tests for the Silver-layer cleaning logic.

Runs against a tiny in-memory Spark DataFrame -- no real data lake, no
cloud account, no dependency on prior pipeline steps. This is exactly
what runs in CI on every push (see .github/workflows/ci.yml).
"""

import sys
import os

import pytest
from pyspark.sql import SparkSession

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.silver.clean_transform import clean  # noqa: E402

TEST_CONFIG = {
    "pipeline": {
        "min_fare_amount": 0.0,
        "max_trip_distance_miles": 200,
        "min_passenger_count": 1,
        "max_passenger_count": 6,
    }
}


@pytest.fixture(scope="module")
def spark():
    session = (
        SparkSession.builder.master("local[2]")
        .appName("pytest-silver")
        .getOrCreate()
    )
    yield session
    session.stop()


def sample_rows():
    return [
        # valid row
        ("2026-08-01T08:00:00", "2026-08-01T08:15:00", 1, 3.2, 12.5, 2.0, "credit_card", "Manhattan-Midtown", "Queens-LIC"),
        # invalid: negative fare -> must be dropped
        ("2026-08-01T09:00:00", "2026-08-01T09:10:00", 1, 2.0, -8.0, 0.0, "cash", "Brooklyn-DUMBO", "Manhattan-Midtown"),
        # invalid: passenger_count out of allowed range -> must be dropped
        ("2026-08-01T10:00:00", "2026-08-01T10:20:00", 9, 4.1, 15.0, 3.0, "credit_card", "Queens-Astoria", "Bronx-Concourse"),
        # invalid: null passenger_count -> must be dropped
        ("2026-08-01T11:00:00", "2026-08-01T11:05:00", None, 1.0, 6.0, 1.0, "mobile_wallet", "Manhattan-Financial", "Manhattan-Midtown"),
        # exact duplicate of the first valid row -> must be de-duplicated
        ("2026-08-01T08:00:00", "2026-08-01T08:15:00", 1, 3.2, 12.5, 2.0, "credit_card", "Manhattan-Midtown", "Queens-LIC"),
    ]


COLUMNS = [
    "pickup_datetime", "dropoff_datetime", "passenger_count", "trip_distance",
    "fare_amount", "tip_amount", "payment_type", "pickup_zone", "dropoff_zone",
]


def test_clean_drops_invalid_and_duplicate_rows(spark):
    df = spark.createDataFrame(sample_rows(), COLUMNS)
    result = clean(df, TEST_CONFIG)

    assert result.count() == 1, "only the single valid, de-duplicated row should survive"

    row = result.collect()[0]
    assert row.fare_amount == 12.5
    assert row.passenger_count == 1
    assert row.trip_date is not None
    assert row.trip_duration_minutes == pytest.approx(15.0, abs=0.01)


def test_clean_computes_trip_duration_in_minutes(spark):
    df = spark.createDataFrame([sample_rows()[0]], COLUMNS)
    result = clean(df, TEST_CONFIG)
    assert result.collect()[0].trip_duration_minutes == pytest.approx(15.0, abs=0.01)
