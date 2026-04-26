#!/usr/bin/env python3
"""Build county_data.parquet and county_map.parquet from Census sources.

Run from the repository root:
    uv run python data-raw/build_counties.py
"""

from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import duckdb
import polars as pl
import requests

STATE_LOOKUP = {
    "01": ("AL", "South"), "02": ("AK", "West"), "04": ("AZ", "West"),
    "05": ("AR", "South"), "06": ("CA", "West"), "08": ("CO", "West"),
    "09": ("CT", "Northeast"), "10": ("DE", "South"),
    "11": ("DC", "South"), "12": ("FL", "South"), "13": ("GA", "South"),
    "15": ("HI", "West"), "16": ("ID", "West"), "17": ("IL", "Midwest"),
    "18": ("IN", "Midwest"), "19": ("IA", "Midwest"),
    "20": ("KS", "Midwest"), "21": ("KY", "South"),
    "22": ("LA", "South"), "23": ("ME", "Northeast"),
    "24": ("MD", "South"), "25": ("MA", "Northeast"),
    "26": ("MI", "Midwest"), "27": ("MN", "Midwest"),
    "28": ("MS", "South"), "29": ("MO", "Midwest"),
    "30": ("MT", "West"), "31": ("NE", "Midwest"),
    "32": ("NV", "West"), "33": ("NH", "Northeast"),
    "34": ("NJ", "Northeast"), "35": ("NM", "West"),
    "36": ("NY", "Northeast"), "37": ("NC", "South"),
    "38": ("ND", "Midwest"), "39": ("OH", "Midwest"),
    "40": ("OK", "South"), "41": ("OR", "West"),
    "42": ("PA", "Northeast"), "44": ("RI", "Northeast"),
    "45": ("SC", "South"), "46": ("SD", "Midwest"),
    "47": ("TN", "South"), "48": ("TX", "South"),
    "49": ("UT", "West"), "50": ("VT", "Northeast"),
    "51": ("VA", "South"), "53": ("WA", "West"),
    "54": ("WV", "South"), "55": ("WI", "Midwest"),
    "56": ("WY", "West"),
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


def _acs_county_data(year: int, api_key: str | None = None) -> pl.DataFrame:
    acs_vars = {
        "B01003_001E": "pop",
        "B01001B_001E": "black",
        "B01001A_001E": "white",
        "B01001H_001E": "nh_white",
        "B01001I_001E": "hispanic",
        "B01001D_001E": "asian",
    }
    params = {
        "get": "NAME," + ",".join(acs_vars),
        "for": "county:*",
    }
    if api_key is not None:
        params["key"] = api_key

    response = requests.get(
        f"https://api.census.gov/data/{year}/acs/acs5",
        params=params,
        timeout=120,
    )
    response.raise_for_status()
    rows = response.json()

    return (
        pl.DataFrame(rows[1:], schema=rows[0], orient="row")
        .rename(acs_vars)
        .with_columns(
            pl.col(list(acs_vars.values())).cast(pl.Int64),
            id=pl.col("state") + pl.col("county"),
        )
        .drop("county")
        .filter(pl.col("state") != "72")
    )


def build_counties(
    year: int = 2023,
    resolution: str = "500k",
    out_dir: str | Path = "src/socviz_data/_data",
    cache_dir: str | Path = "data-raw/_cache/census",
    api_key: str | None = None,
    shift: bool = True,
    crop: bool = False,
    simplify_tolerance: float | None = 1000,
    legacy_county_data_path: str | Path = "src/socviz_data/_data/county_data.parquet",
) -> dict[str, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    county_data_path = out_dir / "county_data.parquet"
    county_map_path = out_dir / "county_map.parquet"

    boundaries = _county_boundary_path(year, resolution, cache_dir)
    acs = _acs_county_data(year, api_key=api_key)

    states = pl.DataFrame(
        {
            "state": list(STATE_LOOKUP),
            "st": [v[0] for v in STATE_LOOKUP.values()],
            "census_region": [v[1] for v in STATE_LOOKUP.values()],
        }
    )
    state_fips_sql = ", ".join(f"'{state}'" for state in STATE_LOOKUP)

    con = duckdb.connect()
    try:
        con.sql("LOAD spatial")
    except Exception:
        con.sql("INSTALL spatial")
        con.sql("LOAD spatial")

    con.sql(f"""
        CREATE OR REPLACE TABLE counties_raw AS
        SELECT
            GEOID AS id,
            STATEFP AS state,
            ST_Transform(geom, 'EPSG:4269', 'ESRI:102003', always_xy := true) AS geom_us,
            ST_Transform(geom, 'EPSG:4269', 'EPSG:3338', always_xy := true) AS geom_ak,
            ST_Transform(geom, 'EPSG:4269', 'ESRI:102007', always_xy := true) AS geom_hi
        FROM ST_Read('{boundaries.as_posix()}')
        WHERE STATEFP IN ({state_fips_sql})
    """)

    con.sql("""
        CREATE OR REPLACE TABLE lower48_bbox AS
        SELECT
            ST_XMin(ST_Extent_Agg(geom_us)) AS xmin,
            ST_XMax(ST_Extent_Agg(geom_us)) AS xmax,
            ST_YMin(ST_Extent_Agg(geom_us)) AS ymin,
            ST_YMax(ST_Extent_Agg(geom_us)) AS ymax
        FROM counties_raw
        WHERE state NOT IN ('02', '15')
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
                ST_X(ST_Centroid(ST_Union_Agg(geom_ak) FILTER (WHERE state = '02'))) AS ak_x,
                ST_Y(ST_Centroid(ST_Union_Agg(geom_ak) FILTER (WHERE state = '02'))) AS ak_y,
                ST_X(ST_Centroid(ST_Union_Agg(geom_hi) FILTER (WHERE state = '15'))) AS hi_x,
                ST_Y(ST_Centroid(ST_Union_Agg(geom_hi) FILTER (WHERE state = '15'))) AS hi_y
            FROM counties_raw
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
                WHEN state = '02' THEN
                    ST_Affine(
                        geom_ak,
                        0.5, 0.0, 0.0, 0.5,
                        ak_target_x - 0.5 * ak_x,
                        ak_target_y - 0.5 * ak_y
                    )
                WHEN state = '15' THEN
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
        CREATE OR REPLACE TABLE counties_projected AS
        SELECT
            id,
            state,
            {geometry_expr} AS geometry
        FROM counties_raw, shift_params
    """)

    geom_for_map = "geometry"
    if crop:
        geom_for_map = """
            ST_Intersection(
                geometry,
                ST_MakeEnvelope(-2500000, -1697746, 2258200, 1565782)
            )
        """

    if simplify_tolerance is not None and simplify_tolerance > 0:
        geom_for_map = f"ST_Simplify({geom_for_map}, {float(simplify_tolerance)})"

    con.sql(f"""
        CREATE OR REPLACE TABLE counties_map_geom AS
        SELECT
            id,
            {geom_for_map} AS geometry
        FROM counties_projected
        WHERE NOT ST_IsEmpty({geom_for_map})
    """)

    area = con.sql("""
        SELECT
            id,
            ST_Area(geometry) / 2589988.110336 AS area_sqmi
        FROM counties_projected
    """).pl()

    county_data = (
        acs.join(area, on="id", how="left")
        .join(states, on="state", how="left")
        .with_columns(
            name=pl.col("NAME").str.replace(r", .*$", ""),
            pop_dens_value=pl.col("pop") / pl.col("area_sqmi"),
            pct_black_value=pl.col("black") / pl.col("pop") * 100,
        )
        .with_columns(
            pop_dens=(
                pl.when(pl.col("pop_dens_value") < 10).then(pl.lit("[    0,   10)"))
                .when(pl.col("pop_dens_value") < 50).then(pl.lit("[   10,   50)"))
                .when(pl.col("pop_dens_value") < 100).then(pl.lit("[   50,  100)"))
                .when(pl.col("pop_dens_value") < 500).then(pl.lit("[  100,  500)"))
                .when(pl.col("pop_dens_value") < 1000).then(pl.lit("[  500, 1000)"))
                .when(pl.col("pop_dens_value") < 5000).then(pl.lit("[ 1000, 5000)"))
                .otherwise(pl.lit("[ 5000,71672]"))
            ),
            pct_black=(
                pl.when(pl.col("pct_black_value") < 2).then(pl.lit("[ 0.0, 2.0)"))
                .when(pl.col("pct_black_value") < 5).then(pl.lit("[ 2.0, 5.0)"))
                .when(pl.col("pct_black_value") < 10).then(pl.lit("[ 5.0,10.0)"))
                .when(pl.col("pct_black_value") < 15).then(pl.lit("[10.0,15.0)"))
                .when(pl.col("pct_black_value") < 25).then(pl.lit("[15.0,25.0)"))
                .when(pl.col("pct_black_value") < 50).then(pl.lit("[25.0,50.0)"))
                .otherwise(pl.lit("[50.0,85.3]"))
            ),
        )
        .select(
            "id", "name", "st", "state", "census_region",
            "area_sqmi", "white", "black", "asian", "nh_white", "hispanic",
            "pop", "pop_dens_value", "pct_black_value", "pop_dens", "pct_black",
        )
    )

    legacy_path = Path(legacy_county_data_path) if legacy_county_data_path else None
    if legacy_path and legacy_path.exists():
        legacy_source = pl.read_parquet(legacy_path)
        legacy = legacy_source.select(
            [c for c in ["id", "su_gun6", "pop_dens6"] if c in legacy_source.columns]
        )
        if legacy.columns != ["id"]:
            county_data = county_data.join(legacy, on="id", how="left")

    county_data.write_parquet(county_data_path)

    con.sql(f"""
        COPY (
            WITH
            raw_parts AS (
                SELECT
                    id,
                    dump.geom AS geom,
                    dump.path AS path
                FROM counties_map_geom,
                UNNEST(ST_Dump(geometry)) AS t(dump)
            ),
            parts AS (
                SELECT
                    id,
                    geom,
                    row_number() OVER (
                        PARTITION BY id
                        ORDER BY CAST(path AS VARCHAR)
                    ) AS piece
                FROM raw_parts
                WHERE ST_GeometryType(geom) = 'POLYGON'
            ),
            rings AS (
                SELECT
                    id,
                    piece,
                    ST_ExteriorRing(geom) AS ring
                FROM parts
            ),
            points AS (
                SELECT
                    id,
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
                '0500000US' || id || '.' || piece::VARCHAR AS "group",
                id
            FROM points
            ORDER BY id, piece, ord
        )
        TO '{county_map_path.as_posix()}'
        (FORMAT PARQUET)
    """)

    return {
        "county_data": county_data_path,
        "county_map": county_map_path,
    }


if __name__ == "__main__":
    print(build_counties())
