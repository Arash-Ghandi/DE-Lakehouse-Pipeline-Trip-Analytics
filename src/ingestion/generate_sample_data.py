"""
Generates a synthetic "taxi trip" dataset shaped like the public NYC TLC
trip record schema, so the pipeline is fully reproducible without needing
to download anything or hold cloud credentials.

In a real deployment, this script is replaced by a real ingestion step
(e.g. pulling from the NYC TLC public dataset, a REST API, or a message
queue) -- everything downstream (bronze/silver/gold) is unaffected because
it only cares about the raw CSV schema, not where it came from.

Usage:
    python src/ingestion/generate_sample_data.py --rows 50000 --out data/raw
"""

import argparse
import os
import random
from datetime import datetime, timedelta

import pandas as pd

ZONES = [
    "Manhattan-Midtown", "Manhattan-Financial", "Brooklyn-Williamsburg",
    "Brooklyn-DUMBO", "Queens-LIC", "Queens-Astoria", "Bronx-Concourse",
    "Staten Island-StGeorge",
]

PAYMENT_TYPES = ["credit_card", "cash", "mobile_wallet"]


def generate_trips(n_rows: int, start_date: datetime) -> pd.DataFrame:
    rows = []
    for _ in range(n_rows):
        pickup = start_date + timedelta(
            days=random.randint(0, 29),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        trip_minutes = max(1, int(random.gauss(14, 8)))
        dropoff = pickup + timedelta(minutes=trip_minutes)

        distance = round(max(0.1, random.gauss(3.2, 2.5)), 2)
        fare = round(max(2.5, distance * random.uniform(2.2, 3.4) + random.uniform(-1, 3)), 2)
        tip = round(max(0, fare * random.uniform(0, 0.25)), 2)

        # deliberately inject a small amount of dirty data so the Silver
        # layer has something real to clean (negative fares, nulls, etc.)
        if random.random() < 0.01:
            fare = -fare
        passenger_count = random.choice([1, 1, 1, 2, 2, 3, 4, None if random.random() < 0.005 else 1])

        rows.append({
            "pickup_datetime": pickup.isoformat(),
            "dropoff_datetime": dropoff.isoformat(),
            "passenger_count": passenger_count,
            "trip_distance": distance,
            "fare_amount": fare,
            "tip_amount": tip,
            "payment_type": random.choice(PAYMENT_TYPES),
            "pickup_zone": random.choice(ZONES),
            "dropoff_zone": random.choice(ZONES),
        })
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=50000)
    parser.add_argument("--out", type=str, default="data/raw")
    parser.add_argument("--month", type=str, default="2026-08",
                         help="YYYY-MM, used to name the file and seed pickup dates")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    start_date = datetime.strptime(args.month, "%Y-%m")
    df = generate_trips(args.rows, start_date)

    out_path = os.path.join(args.out, f"trips_{args.month}.csv")
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df):,} rows to {out_path}")


if __name__ == "__main__":
    main()
