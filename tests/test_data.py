import polars as pl

from socviz_pl import available_data, data_path, load_data


def test_available_data_includes_book_data():
    names = available_data()
    assert "gss_sm" in names
    assert "county_map" in names


def test_load_data_returns_polars_dataframe():
    df = load_data("gss_sm")
    assert isinstance(df, pl.DataFrame)
    assert df.height > 0


def test_data_path_points_to_packaged_parquet():
    path = data_path("gss_sm")
    assert path.name == "gss_sm.parquet"
    assert path.exists()


def test_unknown_dataset_lists_available_names():
    try:
        load_data("not_a_dataset")
    except KeyError as err:
        assert "gss_sm" in str(err)
    else:
        raise AssertionError("load_data should reject unknown datasets")
