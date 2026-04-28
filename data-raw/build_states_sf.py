#!/usr/bin/env python3
"""Build states_sf.parquet by dissolving county boundaries to state level.

Uses the same Census county shapefiles and AK/HI repositioning as county_map.

Run from the repository root:
    uv run python data-raw/build_states_sf.py
"""

from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import duckdb
import polars as pl
import requests

STATE_NAMES = {
    "01": "Alabama", "02": "Alaska", "04": "Arizona",
    "05": "Arkansas", "06": "California", "08": "Colorado",
    "09": "Connecticut", "10": "Delaware", "11": "District of Columbia",
    "12": "Florida", "13": "Georgia", "15": "Hawaii",
    "16": "Idaho", "17": "Illinois", "18": "Indiana",
    "19": "Iowa", "20": "Kansas", "21": "Kentucky",
    "22": "Louisiana", "23": "Maine", "24": "Maryland",
    "25": "Massachusetts", "26": "Michigan", "27": "Minnesota",
    "28": "Mississippi", "29": "Missouri", "30": "Montana",
    "31": "Nebraska", "32": "Nevada", "33": "New Hampshire",
    "34": "New Jersey", "35": "New Mexico", "36": "New York",
    "37": "North Carolina", "38": "North Dakota", "39": "Ohio",
    "40": "Oklahoma", "41": "Oregon", "42": "Pennsylvania",
    "44": "Rhode Island", "45": "South Carolina", "46": "South Dakota",
    "47": "Tennessee", "48": "Texas", "49": "Utah",
    "50": "Vermont", "51": "Virginia", "53": "Washington",
    "54": "West Virginia", "55": "Wisconsin", "56": "Wyoming",
}


def _download_file(url: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return path

    response = requests.get(url, timeout=120)
    response.raise_for_status()
    path.write_bytes(response.content)
    return path


def _county_boundary_path(year: int, resolution: str, cache_dir: str | Path) -> Path:
    cache_dir = Path(cache_dir)
    zip_path = cache_dir / f"cb_{year}_us_county_{resolution}.zip"
    shp_dir = cache_dir / f"cb_{year}_us_county_{resolution}"
    shp_path = shp_dir / f"cb_{year}_us_county_{resolution}.shp"
    url = (
        f"https://www2.census.gov/geo/tiger/GENZ{year}/shp/"
        f"cb_{year}_us_county_{resolution}.zip"
    )

    _download_file(url, zip_path)
    if not shp_path.exists():
        shp_dir.mkdir(parents=True, exist_ok=True)
        with ZipFile(zip_path) as zf:
            zf.extractall(shp_dir)
    return shp_path


def build_states_sf(
    year: int = 2023,
    resolution: str = "500k",
    out_dir: str | Path = "src/socviz_data/_data",
    cache_dir: str | Path = "data-raw/_cache/census",
    shift: bool = True,
    simplify_tolerance: float | None = 1000,
) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    states_sf_path = out_dir / "states_sf.parquet"

    boundaries = _county_boundary_path(year, resolution, cache_dir)

    state_meta = pl.DataFrame(
        {
            "fips": list(STATE_NAMES),
            "state": list(STATE_NAMES.values()),
        }
    )

    state_fips_sql = ", ".join(f"'{fips}'" for fips in STATE_NAMES)

    con = duckdb.connect()
    try:
        con.sql("LOAD spatial")
    except Exception:
        con.sql("INSTALL spatial")
        con.sql("LOAD spatial")

    con.sql(f"""
        CREATE OR REPLACE TABLE states_raw AS
        SELECT
            STATEFP AS fips,
            ST_Union_Agg(
                ST_Transform(geom, 'EPSG:4269', 'ESRI:102003', always_xy := true)
            ) AS geom_us,
            ST_Union_Agg(
                ST_Transform(geom, 'EPSG:4269', 'EPSG:3338', always_xy := true)
            ) AS geom_ak,
            ST_Union_Agg(
                ST_Transform(geom, 'EPSG:4269', 'ESRI:102007', always_xy := true)
            ) AS geom_hi
        FROM ST_Read('{boundaries.as_posix()}')
        WHERE STATEFP IN ({state_fips_sql})
        GROUP BY STATEFP
    """)

    con.sql("""
        CREATE OR REPLACE TABLE lower48_bbox AS
        SELECT
            ST_XMin(ST_Extent_Agg(geom_us)) AS xmin,
            ST_XMax(ST_Extent_Agg(geom_us)) AS xmax,
            ST_YMin(ST_Extent_Agg(geom_us)) AS ymin,
            ST_YMax(ST_Extent_Agg(geom_us)) AS ymax
        FROM states_raw
        WHERE fips NOT IN ('02', '15')
    """)

    con.sql("""
        CREATE OR REPLACE TABLE shift_params AS
        WITH
        bb AS (
            SELECT *, xmax - xmin AS width, ymax - ymin AS height
            FROM lower48_bbox
        ),
        centroids AS (
            SELECT
                ST_X(ST_Centroid(ST_Union_Agg(geom_ak) FILTER (WHERE fips = '02'))) AS ak_x,
                ST_Y(ST_Centroid(ST_Union_Agg(geom_ak) FILTER (WHERE fips = '02'))) AS ak_y,
                ST_X(ST_Centroid(ST_Union_Agg(geom_hi) FILTER (WHERE fips = '15'))) AS hi_x,
                ST_Y(ST_Centroid(ST_Union_Agg(geom_hi) FILTER (WHERE fips = '15'))) AS hi_y
            FROM states_raw
        )
        SELECT
            bb.xmin + 0.08 * bb.width AS ak_target_x,
            bb.ymin + 0.07 * bb.height AS ak_target_y,
            bb.xmin + 0.35 * bb.width AS hi_target_x,
            bb.ymin + 0.00 * bb.height AS hi_target_y,
            centroids.*
        FROM bb, centroids
    """)

    if shift:
        geometry_expr = """
            CASE
                WHEN fips = '02' THEN
                    ST_Affine(
                        geom_ak,
                        0.5, 0.0, 0.0, 0.5,
                        ak_target_x - 0.5 * ak_x,
                        ak_target_y - 0.5 * ak_y
                    )
                WHEN fips = '15' THEN
                    ST_Affine(
                        geom_hi,
                        1.5, 0.0, 0.0, 1.5,
                        hi_target_x - 1.5 * hi_x,
                        hi_target_y - 1.5 * hi_y
                    )
                ELSE geom_us
            END
        """
    else:
        geometry_expr = "geom_us"

    con.sql(f"""
        CREATE OR REPLACE TABLE states_projected AS
        SELECT
            fips,
            {geometry_expr} AS geometry
        FROM states_raw, shift_params
    """)

    geom_for_map = "geometry"
    if simplify_tolerance is not None and simplify_tolerance > 0:
        geom_for_map = f"ST_Simplify({geom_for_map}, {float(simplify_tolerance)})"

    con.sql(f"""
        CREATE OR REPLACE TABLE states_map_geom AS
        SELECT
            fips,
            {geom_for_map} AS geometry
        FROM states_projected
        WHERE NOT ST_IsEmpty({geom_for_map})
    """)

    con.sql(f"""
        COPY (
            WITH
            raw_parts AS (
                SELECT
                    fips,
                    dump.geom AS geom,
                    dump.path AS path
                FROM states_map_geom,
                UNNEST(ST_Dump(geometry)) AS t(dump)
            ),
            parts AS (
                SELECT
                    fips,
                    geom,
                    row_number() OVER (
                        PARTITION BY fips
                        ORDER BY CAST(path AS VARCHAR)
                    ) AS piece
                FROM raw_parts
                WHERE ST_GeometryType(geom) = 'POLYGON'
            ),
            rings AS (
                SELECT
                    fips,
                    piece,
                    ST_ExteriorRing(geom) AS ring
                FROM parts
            ),
            points AS (
                SELECT
                    fips,
                    piece,
                    i AS ord,
                    ST_PointN(ring, i::INTEGER) AS pt
                FROM rings,
                generate_series(1, ST_NumPoints(ring)::INTEGER) AS t(i)
            )
            SELECT
                ST_X(pt) AS long,
                ST_Y(pt) AS lat,
                ord::DOUBLE AS "order",
                false AS hole,
                piece::VARCHAR AS piece,
                '0400000US' || fips || '.' || piece::VARCHAR AS "group",
                fips
            FROM points
            ORDER BY fips, piece, ord
        )
        TO '{states_sf_path.as_posix()}'
        (FORMAT PARQUET)
    """)

    # Join state names and overwrite
    geom_df = pl.read_parquet(states_sf_path)
    (
        geom_df
        .join(state_meta, on="fips", how="left")
        .select(["long", "lat", "order", "hole", "piece", "group", "state"])
        .write_parquet(states_sf_path)
    )

    return states_sf_path


if __name__ == "__main__":
    print(build_states_sf())
