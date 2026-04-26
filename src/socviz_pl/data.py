from __future__ import annotations

from importlib.resources import as_file, files
from pathlib import Path

import polars as pl

_DATA_PACKAGE = "socviz_data"


def available_data() -> list[str]:
    """Return packaged dataset names available via load_data()."""

    data_dir = files(_DATA_PACKAGE).joinpath("_data")
    return sorted(
        item.name.removesuffix(".parquet")
        for item in data_dir.iterdir()
        if item.name.endswith(".parquet")
    )


def data_path(name: str) -> Path:
    """Return a filesystem path for a packaged Parquet dataset."""

    data_file = files(_DATA_PACKAGE).joinpath("_data", f"{name}.parquet")
    if not data_file.is_file():
        available = ", ".join(available_data())
        raise KeyError(f"Unknown dataset {name!r}. Available datasets: {available}")

    with as_file(data_file) as path:
        return Path(path)


def load_data(name: str) -> pl.DataFrame:
    """Load a packaged dataset as a Polars DataFrame."""

    data_file = files(_DATA_PACKAGE).joinpath("_data", f"{name}.parquet")
    if not data_file.is_file():
        available = ", ".join(available_data())
        raise KeyError(f"Unknown dataset {name!r}. Available datasets: {available}")

    with data_file.open("rb") as f:
        try:
            return pl.read_parquet(f)
        except pl.exceptions.ComputeError as err:
            if "invalid UTF-8" not in str(err):
                raise
            f.seek(0)
            return pl.read_parquet(f, use_pyarrow=True)
