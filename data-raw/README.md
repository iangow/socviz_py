# Data Preparation

This directory is the maintainer-facing home for scripts that regenerate the packaged Parquet data. This follows the same convention as `data-raw/` in R packages: the files here explain and reproduce the data bundled under `src/socviz_data/_data`, but they are not part of the runtime import API.

## R-originated book data

Most small data files come from data objects in the upstream `socviz` R package. Regenerate them with:

```sh
Rscript data-raw/convert_socviz_rda_to_parquet.R
```

That script also writes `us_states.parquet` from `ggplot2::map_data("state")`.

## County map data

The county files are built from Census cartographic county boundaries and ACS 5-year county data. Regenerate them with:

```sh
uv run python data-raw/build_counties.py
```

The script writes:

- `src/socviz_data/_data/county_data.parquet`
- `src/socviz_data/_data/county_map.parquet`

`county_data.parquet` preserves `su_gun6` and `pop_dens6` from the existing packaged file when present, because those variables do not come from ACS.
