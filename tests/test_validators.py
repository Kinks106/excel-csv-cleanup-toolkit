import pandas as pd

from cleanup_tool import validators


def test_required_columns_missing():
    df = pd.DataFrame({"a": [1]})
    missing = validators.validate_required_columns(df, ["a", "b"])
    assert missing == ["b"]


def test_validate_types_flags_non_numeric():
    df = pd.DataFrame({"n": ["1", "2", "x"]})
    issues = validators.validate_types(df, {"n": "float"})
    assert issues["n"]["non_numeric"] == 1


def test_validate_types_flags_non_integer():
    df = pd.DataFrame({"q": ["1", "2.5", "3"]})
    issues = validators.validate_types(df, {"q": "int"})
    assert issues["q"]["non_integer"] == 1


def test_validate_overall_ok():
    df = pd.DataFrame({"order_id": ["1", "2"], "amount": ["10.0", "20.0"]})
    res = validators.validate(df, ["order_id"], {"order_id": "int", "amount": "float"})
    assert res.ok is True
    assert res.errors == []


def test_validate_overall_error_on_missing_required():
    df = pd.DataFrame({"a": ["1"]})
    res = validators.validate(df, ["order_id"], {})
    assert res.ok is False
    assert res.errors
