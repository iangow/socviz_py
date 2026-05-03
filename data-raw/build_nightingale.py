#!/usr/bin/env python3
"""Build nightingale.parquet — Florence Nightingale's Crimean War mortality data.

Data source: Nightingale, F. (1858). Notes on Matters Affecting the Health,
Efficiency, and Hospital Administration of the British Army. Harrison and Sons.

Also available in the R HistData package:
  Friendly, M. (2025). HistData: Data Sets from the History of Statistics
  and Data Visualization. R package version 0.9-3.
  https://CRAN.R-project.org/package=HistData

Run from the repository root:
    uv run python data-raw/build_nightingale.py
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

OUTPUT = (
    Path(__file__).parent.parent
    / "src" / "socviz_data" / "_data" / "nightingale.parquet"
)


def build() -> pl.DataFrame:
    months_p1 = [
        "1854-Apr", "1854-May", "1854-Jun", "1854-Jul", "1854-Aug", "1854-Sep",
        "1854-Oct", "1854-Nov", "1854-Dec", "1855-Jan", "1855-Feb", "1855-Mar",
    ]
    months_p2 = [
        "1855-Apr", "1855-May", "1855-Jun", "1855-Jul", "1855-Aug", "1855-Sep",
        "1855-Oct", "1855-Nov", "1855-Dec", "1856-Jan", "1856-Feb", "1856-Mar",
    ]
    return pl.concat([
        pl.DataFrame({
            "month": months_p1,
            "period": "April 1854 – March 1855",
            "diseases":     [1, 12, 11, 359, 828, 788, 503, 844, 1725, 2761, 2120, 1205],
            "wounds":       [0,  0,  0,   0,   1,  81, 132, 287,  114,   83,   42,   32],
            "other_causes": [5,  9,  6,  23,  30,  70, 128, 106,  131,  324,  361,  172],
        }),
        pl.DataFrame({
            "month": months_p2,
            "period": "April 1855 – March 1856",
            "diseases":     [477, 508, 802, 382, 483, 189, 128, 178, 91, 42, 24, 15],
            "wounds":       [ 48,  49, 209, 134, 164, 276,  53,  33, 18,  2,  0,  0],
            "other_causes": [ 57,  37,  31,  33,  25,  20,  18,  32, 28, 48, 19, 35],
        }),
    ]).with_columns(month=pl.col("month").str.to_date("%Y-%b"))


if __name__ == "__main__":
    df = build()
    df.write_parquet(OUTPUT)
    print(f"Written {df.height} rows to {OUTPUT}")
    print(df)
