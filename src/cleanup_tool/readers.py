"""File readers for CSV/TSV and Excel inputs.

Everything is read as text (dtype=str) so that raw values are preserved and
the cleaning/validation layers stay in full control of typing. Blank lines are
kept so that the "remove empty rows" step can count and report them.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

CSV_LIKE = {".csv", ".txt"}
TSV_LIKE = {".tsv"}
EXCEL_LIKE = {".xlsx", ".xlsm", ".xls"}
SUPPORTED = CSV_LIKE | TSV_LIKE | EXCEL_LIKE


def read_table(path: Any, sheet: Any = 0) -> pd.DataFrame:
    """Read a CSV/TSV/Excel file into a DataFrame of strings.

    Raises FileNotFoundError if the path is missing and ValueError for an
    unsupported file type.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {p}")

    ext = p.suffix.lower()
    if ext in CSV_LIKE:
        return pd.read_csv(p, dtype=str, keep_default_na=True, skip_blank_lines=False)
    if ext in TSV_LIKE:
        return pd.read_csv(p, sep="\t", dtype=str, keep_default_na=True, skip_blank_lines=False)
    if ext in EXCEL_LIKE:
        return pd.read_excel(p, sheet_name=sheet, dtype=str)

    raise ValueError(
        f"Unsupported input type '{ext}'. Supported: {sorted(SUPPORTED)}."
    )
