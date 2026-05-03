# Data Preparation

This directory is the maintainer-facing home for scripts that regenerate the packaged Parquet data. This follows the same convention as `data-raw/` in R packages: the files here explain and reproduce the data bundled under `src/socviz_data/_data`, but they are not part of the runtime import API.

## R-originated book data

Most small data files come from data objects in the upstream `socviz` R package. Regenerate them with:

```sh
Rscript data-raw/convert_socviz_rda_to_parquet.R
```

That script also writes `us_states.parquet` from `ggplot2::map_data("state")`.

## State simple-feature vertices

`states_sf.parquet` is built from the `geoda.ncovr` geometry in `geodatasets`.
It stores one row per state exterior-ring vertex, with longitude and latitude
left unprojected so examples can choose a projection when plotting. Regenerate
it with:

```sh
uv run python data-raw/build_states_sf.py
```

## County map data

The county files are built from Census cartographic county boundaries and ACS 5-year county data. Regenerate them with:

```sh
uv run python data-raw/build_counties.py
```

The script writes:

- `src/socviz_data/_data/county_data.parquet`
- `src/socviz_data/_data/county_map.parquet`

`county_data.parquet` preserves `su_gun6` and `pop_dens6` from the existing packaged file when present, because those variables do not come from ACS.

## Climate circles

`meteo_yday.parquet` contains daily average temperature ranges for nine US
cities over 1991-2020, prepared for climate-circle examples. Regenerate it with:

```sh
uv run python data-raw/build_meteo_yday.py
```

The script uses Dominic Royé's climate-circles data ZIP and replaces Denver
with Boston Logan daily summaries from NOAA NCEI.
