import numpy as np
import pandas as pd

from cleanup_tool import cleaners


def test_normalize_column_names():
    df = pd.DataFrame(columns=["Order ID", " Unit Price ", "Region!!"])
    out, info = cleaners.normalize_column_names(df)
    assert list(out.columns) == ["order_id", "unit_price", "region"]
    assert info["renamed"]["Order ID"] == "order_id"


def test_normalize_column_names_dedupes_collisions():
    df = pd.DataFrame(columns=["A", "a", "a "])
    out, _ = cleaners.normalize_column_names(df)
    assert list(out.columns) == ["a", "a_1", "a_2"]


def test_remove_empty_rows():
    df = pd.DataFrame({"a": ["1", np.nan, "2"], "b": ["x", np.nan, "y"]})
    out, info = cleaners.remove_empty_rows(df)
    assert info["empty_rows_removed"] == 1
    assert len(out) == 2


def test_remove_duplicates():
    df = pd.DataFrame({"a": ["1", "1", "2"], "b": ["x", "x", "y"]})
    out, info = cleaners.remove_duplicates(df)
    assert info["duplicates_removed"] == 1
    assert len(out) == 2


def test_normalize_text_case():
    df = pd.DataFrame({"r": [" north ", "SOUTH", "South"]})
    out, info = cleaners.normalize_text_case(df, {"r": "upper"})
    assert list(out["r"]) == ["NORTH", "SOUTH", "SOUTH"]
    assert info["text_case_applied"] == {"r": "upper"}


def test_parse_dates_counts_unparseable():
    df = pd.DataFrame({"d": ["2024-01-01", "2024-01-02", "not-a-date"]})
    out, info = cleaners.parse_dates(df, {"d": None})
    assert info["dates_parsed"]["d"]["unparseable"] == 1
    assert pd.isna(out["d"].iloc[2])


def test_handle_missing_fill_value_and_median():
    df = pd.DataFrame({"name": ["a", np.nan], "price": ["10", np.nan]})
    rules = {
        "name": {"strategy": "fill_value", "value": "UNKNOWN"},
        "price": {"strategy": "fill_median"},
    }
    out, info = cleaners.handle_missing_values(df, rules, {"strategy": "leave"})
    assert out["name"].iloc[1] == "UNKNOWN"
    # Only one numeric value (10) -> median 10 fills the gap.
    assert float(out["price"].iloc[1]) == 10.0
    assert info["rows_dropped_for_missing"] == 0


def test_handle_missing_drop_row():
    df = pd.DataFrame({"id": ["1", np.nan, "3"], "v": ["a", "b", "c"]})
    rules = {"id": {"strategy": "drop_row"}}
    out, info = cleaners.handle_missing_values(df, rules, {"strategy": "leave"})
    assert info["rows_dropped_for_missing"] == 1
    assert len(out) == 2
