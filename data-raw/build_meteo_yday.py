#!/usr/bin/env python3
"""Build meteo_yday.parquet for climate-circle examples.

The base data come from Dominic Roye's climate-circles example. His ZIP
contains daily station data for nine US cities. We keep the original city
ordering but replace Denver with Boston Logan daily summaries from NOAA NCEI.

Run from the repository root:
    uv run python data-raw/build_meteo_yday.py
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile

import polars as pl

ROOT = Path(__file__).parent.parent
CACHE = ROOT / "data-raw" / "_cache" / "climate_circles"
OUTPUT = ROOT / "src" / "socviz_data" / "_data" / "meteo_yday.parquet"

ROYE_ZIP_URL = "https://dominicroye.github.io/assets/www/weather_stats_usa.zip"
BOSTON_URL = (
    "https://www.ncei.noaa.gov/access/services/data/v1"
    "?dataset=daily-summaries"
    "&stations=USW00014739"
    "&startDate=1991-01-01"
    "&endDate=2020-12-31"
    "&dataTypes=TAVG,TMAX,TMIN"
    "&units=metric"
    "&format=csv"
    "&includeStationName=true"
)

CITIES = [
    "CHICAGO", "NEW YORK", "MIAMI",
    "HOUSTON", "ATLANTA", "SAN FRANCISCO",
    "SEATTLE", "BOSTON", "LAS VEGAS",
]


def cached_download(url: str, filename: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / filename
    if not path.exists():
        urlretrieve(url, path)
    return path


def daily_average_by_yday(df: pl.DataFrame, name: str, city_order: int) -> pl.DataFrame:
    return (
        df
        .select("DATE", "TAVG", "TMAX", "TMIN")
        .with_columns(pl.col("TAVG", "TMAX", "TMIN").cast(pl.Float64, strict=False))
        .filter(pl.col("DATE").is_between(date(1991, 1, 1), date(2020, 12, 31)))
        .with_columns(
            name=pl.lit(name),
            city_order=pl.lit(city_order, dtype=pl.Int64),
            yd=pl.col("DATE").dt.ordinal_day().cast(pl.Int64),
            tavg=pl.when(pl.col("TAVG").is_null())
                   .then((pl.col("TMAX") + pl.col("TMIN")) / 2)
                   .otherwise(pl.col("TAVG")),
        )
        .group_by("name", "city_order", "yd")
        .agg(
            ta=pl.col("tavg").mean(),
            tmx=pl.col("TMAX").mean(),
            tmin=pl.col("TMIN").mean(),
        )
        .with_columns(date=pl.date(1999, 12, 31) + pl.duration(days=pl.col("yd")))
        .select("name", "city_order", "yd", "date", "ta", "tmx", "tmin")
    )


def build() -> pl.DataFrame:
    roye_zip = cached_download(ROYE_ZIP_URL, "weather_stats_usa.zip")
    boston_csv = cached_download(BOSTON_URL, "boston_logan_daily_1991_2020.csv")

    frames: list[pl.DataFrame] = []
    with ZipFile(roye_zip) as zf:
        for name in sorted(zf.namelist()):
            if name.endswith(".csv"):
                with zf.open(name) as f:
                    frames.append(pl.read_csv(f, try_parse_dates=True, null_values=["", "NA"]))

    meteo = pl.concat(frames, how="diagonal_relaxed")
    stations = meteo.select("NAME").unique(maintain_order=True).get_column("NAME").to_list()
    station_to_city = dict(zip(stations, CITIES, strict=True))
    city_order = {city: i for i, city in enumerate(CITIES)}

    roye_yday = (
        meteo
        .with_columns(name=pl.col("NAME").replace(station_to_city))
        .filter(pl.col("name") != "BOSTON")
        .with_columns(city_order=pl.col("name").replace(city_order).cast(pl.Int64))
        .select("name", "city_order", "DATE", "TAVG", "TMAX", "TMIN")
        .with_columns(pl.col("TAVG", "TMAX", "TMIN").cast(pl.Float64, strict=False))
        .filter(pl.col("DATE").is_between(date(1991, 1, 1), date(2020, 12, 31)))
        .with_columns(
            yd=pl.col("DATE").dt.ordinal_day().cast(pl.Int64),
            tavg=pl.when(pl.col("TAVG").is_null())
                   .then((pl.col("TMAX") + pl.col("TMIN")) / 2)
                   .otherwise(pl.col("TAVG")),
        )
        .group_by("name", "city_order", "yd")
        .agg(
            ta=pl.col("tavg").mean(),
            tmx=pl.col("TMAX").mean(),
            tmin=pl.col("TMIN").mean(),
        )
        .with_columns(date=pl.date(1999, 12, 31) + pl.duration(days=pl.col("yd")))
        .select("name", "city_order", "yd", "date", "ta", "tmx", "tmin")
    )

    boston_yday = daily_average_by_yday(
        pl.read_csv(boston_csv, try_parse_dates=True, null_values=["", "NA"]),
        name="BOSTON",
        city_order=city_order["BOSTON"],
    )

    return (
        roye_yday
        .vstack(boston_yday)
        .sort("city_order", "yd")
    )


if __name__ == "__main__":
    df = build()
    df.write_parquet(OUTPUT)
    print(f"Written {df.height} rows to {OUTPUT}")
    print(df.select("name").unique().sort("name"))
