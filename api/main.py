import os
from datetime import date
from functools import lru_cache
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

GOLD_EXPORT_PATH = os.environ.get(
    "GOLD_EXPORT_PATH",
    os.path.join(os.path.dirname(__file__), "..", "data", "lake", "exports", "daily_zone_revenue.csv"),
)

app = FastAPI(
    title="Lakehouse Pipeline API",
    description="Serves the Gold-layer daily revenue-by-zone aggregate produced by the PySpark pipeline.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ZoneRevenue(BaseModel):
    trip_date: date
    pickup_zone: str
    trip_count: int
    total_fare_revenue: float
    total_tips: float
    avg_trip_duration_minutes: float
    avg_trip_distance_miles: float


class Summary(BaseModel):
    total_trips: int
    total_revenue: float
    total_tips: float
    avg_trip_duration_minutes: float
    date_range_start: date
    date_range_end: date
    zone_count: int


class ZoneTotal(BaseModel):
    pickup_zone: str
    total_revenue: float
    trip_count: int


@lru_cache(maxsize=1)
def _load_data() -> pd.DataFrame:
    if not os.path.exists(GOLD_EXPORT_PATH):
        raise HTTPException(
            status_code=503,
            detail=(
                f"Gold export not found at {GOLD_EXPORT_PATH}. "
                "Run the pipeline first: bronze -> silver -> gold "
                "(see README.md)."
            ),
        )
    df = pd.read_csv(GOLD_EXPORT_PATH, parse_dates=["trip_date"])
    return df


def reload_data() -> pd.DataFrame:
    """Bust the cache -- used by the /refresh endpoint after a new pipeline run."""
    _load_data.cache_clear()
    return _load_data()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/refresh")
def refresh():
    """Re-read the CSV after a fresh pipeline run, without restarting the API."""
    df = reload_data()
    return {"status": "reloaded", "rows": len(df)}


@app.get("/api/zones", response_model=list[str])
def list_zones():
    df = _load_data()
    return sorted(df["pickup_zone"].unique().tolist())


@app.get("/api/summary", response_model=Summary)
def summary(
    zone: Optional[str] = Query(None, description="Filter to a single pickup zone"),
):
    df = _load_data()
    if zone:
        df = df[df["pickup_zone"] == zone]
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data for zone '{zone}'")

    return Summary(
        total_trips=int(df["trip_count"].sum()),
        total_revenue=round(float(df["total_fare_revenue"].sum()), 2),
        total_tips=round(float(df["total_tips"].sum()), 2),
        avg_trip_duration_minutes=round(float(df["avg_trip_duration_minutes"].mean()), 1),
        date_range_start=df["trip_date"].min().date(),
        date_range_end=df["trip_date"].max().date(),
        zone_count=df["pickup_zone"].nunique(),
    )


@app.get("/api/revenue/daily", response_model=list[ZoneRevenue])
def daily_revenue(
    zone: Optional[str] = Query(None, description="Filter to a single pickup zone"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    df = _load_data()
    if zone:
        df = df[df["pickup_zone"] == zone]
    if start_date:
        df = df[df["trip_date"].dt.date >= start_date]
    if end_date:
        df = df[df["trip_date"].dt.date <= end_date]

    df = df.sort_values("trip_date")
    return df.to_dict(orient="records")


@app.get("/api/revenue/by-zone", response_model=list[ZoneTotal])
def revenue_by_zone():
    df = _load_data()
    grouped = (
        df.groupby("pickup_zone")
        .agg(total_revenue=("total_fare_revenue", "sum"), trip_count=("trip_count", "sum"))
        .reset_index()
        .sort_values("total_revenue", ascending=False)
    )
    return grouped.to_dict(orient="records")