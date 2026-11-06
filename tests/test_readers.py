import pandas as pd
import pytest

from cleanup_tool import readers


def test_read_csv_preserves_strings_and_blank_rows(tmp_path):
    p = tmp_path / "in.csv"
    p.write_text("a,b\n1,x\n,\n2,y\n", encoding="utf-8")
    df = readers.read_table(p)
    # Blank row is kept (so it can be counted/removed downstream).
    assert len(df) == 3
    # Values are read as strings.
    assert df["a"].dropna().map(type).eq(str).all()


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        readers.read_table(tmp_path / "nope.csv")


def test_unsupported_extension_raises(tmp_path):
    p = tmp_path / "data.parquet"
    p.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        readers.read_table(p)


def test_read_excel_roundtrip(tmp_path):
    src = pd.DataFrame({"a": ["1", "2"], "b": ["x", "y"]})
    xlsx = tmp_path / "in.xlsx"
    src.to_excel(xlsx, index=False)
    df = readers.read_table(xlsx)
    assert list(df.columns) == ["a", "b"]
    assert len(df) == 2
