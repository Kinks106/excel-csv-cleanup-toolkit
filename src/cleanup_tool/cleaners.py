"""Deterministic cleaning functions.

Each function takes a DataFrame and returns ``(new_df, info)`` where ``info``
is a small dict describing what happened, so the caller can build a complete
report. None of these functions mutate their input in place.
"""
from __future__ import annotations

import re
from typing import Optional

import pandas as pd


def normalize_column_names(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Lowercase, strip, and convert non-alphanumeric runs to single '_'.

    Collisions are de-duplicated by appending a numeric suffix.
    """
    mapping: dict = {}
    new_cols: list = []
    seen: dict = {}
    for col in df.columns:
        base = re.sub(r"[^0-9a-zA-Z]+", "_", str(col).strip().lower()).strip("_")
        base = re.sub(r"_+", "_", base) or "column"
        if base in seen:
            seen[base] += 1
            name = f"{base}_{seen[base]}"
        else:
            seen[base] = 0
            name = base
        mapping[str(col)] = name
        new_cols.append(name)
    out = df.copy()
    out.columns = new_cols
    return out, {"renamed": mapping}


def remove_empty_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Drop rows where every cell is empty/NaN."""
    before = len(df)
    out = df.dropna(how="all").copy()
    return out, {"empty_rows_removed": before - len(out)}


def normalize_text_case(df: pd.DataFrame, text_case: dict) -> tuple[pd.DataFrame, dict]:
    """Strip whitespace and apply lower/upper/title to the named columns."""
    out = df.copy()
    applied: dict = {}
    for col, mode in text_case.items():
        if col not in out.columns:
            continue
        s = out[col].astype("string").str.strip()
        if mode == "lower":
            s = s.str.lower()
        elif mode == "upper":
            s = s.str.upper()
        elif mode == "title":
            s = s.str.title()
        else:
            raise ValueError(f"Unknown text_case mode '{mode}' for column '{col}'.")
        out[col] = s
        applied[col] = mode
    return out, {"text_case_applied": applied}


def parse_dates(df: pd.DataFrame, date_columns: dict) -> tuple[pd.DataFrame, dict]:
    """Coerce the named columns to datetimes; count values that fail to parse."""
    out = df.copy()
    info: dict = {}
    for col, fmt in date_columns.items():
        if col not in out.columns:
            continue
        already_missing = int(out[col].isna().sum())
        if fmt:
            parsed = pd.to_datetime(out[col], format=fmt, errors="coerce")
        else:
            # "mixed" parses each value independently, so varied but valid
            # formats (e.g. "2024-01-05" and "2024/01/09") all parse and only
            # genuinely bad values become NaT. Fall back for older pandas.
            try:
                parsed = pd.to_datetime(out[col], format="mixed", errors="coerce")
            except (ValueError, TypeError):
                parsed = pd.to_datetime(out[col], errors="coerce")
        unparseable = int(parsed.isna().sum()) - already_missing
        out[col] = parsed
        info[col] = {"format": fmt, "unparseable": max(unparseable, 0)}
    return out, {"dates_parsed": info}


def handle_missing_values(
    df: pd.DataFrame, rules: dict, default: dict
) -> tuple[pd.DataFrame, dict]:
    """Apply per-column missing-value strategies, then row drops last.

    Returns info with per-column detail and the number of rows dropped because
    of a ``drop_row`` strategy.
    """
    out = df.copy()
    details: dict = {}

    for col in list(out.columns):
        rule = rules.get(col, default) or {}
        strat = rule.get("strategy", "leave")
        n_missing = int(out[col].isna().sum())

        if strat in ("leave", "drop_row"):
            if n_missing:
                details[col] = {"strategy": strat, "missing": n_missing, "filled": 0}
            continue

        if n_missing == 0:
            continue

        if strat == "fill_value":
            out[col] = out[col].fillna(rule.get("value"))
            details[col] = {"strategy": strat, "filled": n_missing, "value": rule.get("value")}
        elif strat in ("fill_mean", "fill_median"):
            numeric = pd.to_numeric(out[col], errors="coerce")
            raw_val = numeric.mean() if strat == "fill_mean" else numeric.median()
            # Round to kill floating-point noise in the filled value.
            val = round(float(raw_val), 6) if pd.notna(raw_val) else None
            out[col] = numeric.fillna(val)
            details[col] = {"strategy": strat, "filled": n_missing, "value": val}
        elif strat == "fill_mode":
            modes = out[col].mode(dropna=True)
            val = modes.iloc[0] if not modes.empty else None
            out[col] = out[col].fillna(val)
            details[col] = {"strategy": strat, "filled": n_missing, "value": val}

    # Row drops last, so counts are unambiguous.
    drop_cols = [c for c in out.columns if (rules.get(c, default) or {}).get("strategy") == "drop_row"]
    rows_dropped = 0
    if drop_cols:
        before = len(out)
        out = out.dropna(subset=drop_cols).copy()
        rows_dropped = before - len(out)

    return out, {"missing_handling": details, "rows_dropped_for_missing": rows_dropped}


def remove_duplicates(
    df: pd.DataFrame, subset: Optional[list] = None
) -> tuple[pd.DataFrame, dict]:
    """Drop duplicate rows, keeping the first occurrence."""
    before = len(df)
    use_subset = subset if subset else None
    out = df.drop_duplicates(subset=use_subset, keep="first").copy()
    return out, {"duplicates_removed": before - len(out), "subset": use_subset}
