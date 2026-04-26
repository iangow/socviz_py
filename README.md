# socviz_py

Data and helper functions for a Python/Polars companion to *Data Visualization*.

The PyPI distribution is `socviz_py`. The Polars-oriented import package is `socviz_pl`:

```python
import socviz_pl as sv

gapminder = sv.load_data("gss_sm")
sv.available_data()
```

For now, `load_data()` returns Polars DataFrames from bundled Parquet files. A pandas-oriented API can be added later without changing the packaged data layout.

## Data preparation

The packaged Parquet files live under `src/socviz_data/_data`.
The scripts used to regenerate them live in `data-raw/`, following the common R-package convention for source data preparation code.

```sh
Rscript data-raw/convert_socviz_rda_to_parquet.R
uv run python data-raw/build_counties.py
```
