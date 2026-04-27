#!/usr/bin/env python3
"""Build states_sf.parquet from geodatasets state geometry.

Run from the repository root:
    uv run python data-raw/build_states_sf.py
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import geodatasets


def build_states_sf(out_dir: str | Path = "src/socviz_data/_data") -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    states_sf_path = out_dir / "states_sf.parquet"

    path = geodatasets.get_path("geoda.ncovr")
    con = duckdb.connect()
    try:
        con.sql("LOAD spatial")
    except Exception:
        con.sql("INSTALL spatial")
        con.sql("LOAD spatial")

    con.sql(f"""
        CREATE OR REPLACE TABLE states AS
        SELECT
            STATE_NAME AS state,
            ST_Union_Agg(geom) AS geom
        FROM ST_Read('{path}')
        GROUP BY state
        ORDER BY state
    """)

    con.sql(f"""
        COPY (
            WITH
            raw_parts AS (
                SELECT
                    state,
                    dump.geom AS geom,
                    dump.path AS path
                FROM states,
                UNNEST(ST_Dump(geom)) AS t(dump)
            ),
            parts AS (
                SELECT
                    state,
                    geom,
                    row_number() OVER (
                        PARTITION BY state
                        ORDER BY CAST(path AS VARCHAR)
                    ) AS part_id
                FROM raw_parts
            ),
            rings AS (
                SELECT
                    state,
                    state || '_' || part_id::VARCHAR AS group_id,
                    ST_ExteriorRing(geom) AS ring
                FROM parts
            ),
            points AS (
                SELECT
                    state,
                    group_id,
                    i AS ord,
                    ST_PointN(ring, i::INTEGER) AS pt
                FROM rings,
                generate_series(1, ST_NumPoints(ring)::INTEGER) AS t(i)
            )
            SELECT
                state,
                group_id,
                ord,
                ST_X(pt) AS long,
                ST_Y(pt) AS lat
            FROM points
            ORDER BY state, group_id, ord
        )
        TO '{states_sf_path.as_posix()}'
        (FORMAT PARQUET)
    """)

    return states_sf_path


if __name__ == "__main__":
    print(build_states_sf())
