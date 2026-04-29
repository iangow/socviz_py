from __future__ import annotations

from importlib.resources import as_file, files
from pathlib import Path
from zipfile import ZipFile

import polars as pl

_DATA_PACKAGE = "socviz_data"

_FACTORS: dict[str, dict[str, list[str]]] = {
    "gss_sm": {
        "race": ["White", "Black", "Other"],
        "sex": ["Male", "Female"],
        "religion": ["Protestant", "Catholic", "Jewish", "None", "Other"],
        "bigregion": ["Northeast", "Midwest", "South", "West"],
        "marital": ["Married", "Never Married", "Divorced", "Widowed", "Separated"],
        "degree": ["Lt High School", "High School", "Junior College", "Bachelor", "Graduate"],
    },
}


def get_county_boundaries(
    year: int = 2023,
    resolution: str = "500k",
    cache_dir: str | Path = Path.home() / ".cache" / "socviz" / "census",
) -> Path:
    """Download Census cartographic county boundaries and return the .shp path.

    Files are cached in *cache_dir* and only downloaded once.
    """
    import requests

    cache_dir = Path(cache_dir)
    zip_path = cache_dir / f"cb_{year}_us_county_{resolution}.zip"
    shp_dir  = cache_dir / f"cb_{year}_us_county_{resolution}"
    shp_path = shp_dir   / f"cb_{year}_us_county_{resolution}.shp"
    url = (
        f"https://www2.census.gov/geo/tiger/GENZ{year}/shp/"
        f"cb_{year}_us_county_{resolution}.zip"
    )

    cache_dir.mkdir(parents=True, exist_ok=True)
    if not zip_path.exists():
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        zip_path.write_bytes(response.content)

    if not shp_path.exists():
        shp_dir.mkdir(parents=True, exist_ok=True)
        with ZipFile(zip_path) as zf:
            zf.extractall(shp_dir)

    return shp_path


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
            df = pl.read_parquet(f)
        except pl.exceptions.ComputeError as err:
            if "invalid UTF-8" not in str(err):
                raise
            f.seek(0)
            df = pl.read_parquet(f, use_pyarrow=True)

    if name in _FACTORS:
        df = df.with_columns(
            pl.col(col).cast(pl.Enum(levels))
            for col, levels in _FACTORS[name].items()
            if col in df.columns
        )

    return df
