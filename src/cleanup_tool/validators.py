"""Validation (report-only).

Validation never drops rows; it reports problems so a human can decide what to
do. Required-column failures are hard errors; type mismatches are warnings.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class ValidationResult:
    ok: bool
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"ok": self.ok, "errors": self.errors, "warnings": self.warnings}


def validate_required_columns(df: pd.DataFrame, required: list) -> list:
    """Return the list of required columns that are missing."""
    return [c for c in required if c not in df.columns]


def validate_types(df: pd.DataFrame, column_types: dict) -> dict:
    """Report cells that don't match their declared type (ignoring NaN)."""
    issues: dict = {}
    for col, typ in column_types.items():
        if col not in df.columns:
            issues[col] = "column not present"
            continue
        series = df[col].dropna()
        if typ in ("int", "integer"):
            coerced = pd.to_numeric(series, errors="coerce")
            non_numeric = int(coerced.isna().sum())
            non_integer = int((coerced.dropna() % 1 != 0).sum())
            if non_numeric or non_integer:
                issues[col] = {"non_numeric": non_numeric, "non_integer": non_integer}
        elif typ in ("float", "number"):
            coerced = pd.to_numeric(series, errors="coerce")
            non_numeric = int(coerced.isna().sum())
            if non_numeric:
                issues[col] = {"non_numeric": non_numeric}
        elif typ == "date":
            coerced = pd.to_datetime(series, errors="coerce")
            bad = int(coerced.isna().sum())
            if bad:
                issues[col] = {"unparseable_dates": bad}
        elif typ in ("bool", "boolean"):
            allowed = {True, False, "true", "false", "True", "False", "0", "1", 0, 1}
            bad = int((~series.isin(list(allowed))).sum())
            if bad:
                issues[col] = {"non_boolean": bad}
        # str/string: anything is representable as text -> no check
    return issues


def validate(df: pd.DataFrame, required_columns: list, column_types: dict) -> ValidationResult:
    errors: list = []
    warnings: list = []

    missing = validate_required_columns(df, required_columns)
    if missing:
        errors.append(f"Missing required columns: {missing}")

    type_issues = validate_types(df, column_types)
    if type_issues:
        warnings.append({"type_issues": type_issues})

    return ValidationResult(ok=(len(errors) == 0), errors=errors, warnings=warnings)
