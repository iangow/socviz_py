#!/usr/bin/env Rscript

# Convert data objects from the socviz R package repository to Parquet.
# Run from the repository root:
#   Rscript data-raw/convert_socviz_rda_to_parquet.R

required <- c("arrow", "ggplot2")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing) > 0) {
  stop("Install required R packages: ", paste(missing, collapse = ", "))
}

data_dir <- file.path("src", "socviz_data", "_data")
dir.create(data_dir, recursive = TRUE, showWarnings = FALSE)

socviz_data <- c(
  "asasec",
  "farsinvolved",
  "gss_lon",
  "gss_sm",
  "okboomer",
  "studebt",
  "organdata",
  "elections_historic",
  "election",
  "election24",
  "election24_county_df",
  "opiates",
  "titanic",
  "oecd_sum"
)

download_rda <- function(name) {
  url <- paste0(
    "https://github.com/kjhealy/socviz/raw/refs/heads/main/data/",
    name,
    ".rda"
  )
  dest <- file.path(tempdir(), paste0(name, ".rda"))
  download.file(url, dest, mode = "wb", quiet = TRUE)
  dest
}

write_clean_parquet <- function(rda_path, object_name, parquet_path) {
  load(rda_path)
  x <- get(object_name)
  x <- as.data.frame(lapply(x, function(col) {
    if (inherits(col, "Date")) col
    else if (is.factor(col)) as.character(col)
    else if (is.integer(col)) as.integer(col)
    else if (is.numeric(col)) as.numeric(col)
    else as.vector(col)
  }), stringsAsFactors = FALSE)
  arrow::write_parquet(x, parquet_path)
}

for (name in socviz_data) {
  message("Writing ", name, ".parquet")
  write_clean_parquet(
    download_rda(name),
    name,
    file.path(data_dir, paste0(name, ".parquet"))
  )
}

message("Writing us_states.parquet")
us_states <- ggplot2::map_data("state")
arrow::write_parquet(us_states, file.path(data_dir, "us_states.parquet"))
