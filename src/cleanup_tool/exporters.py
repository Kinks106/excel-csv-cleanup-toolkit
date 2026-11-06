"""Output writers for cleaned data."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def _ensure_parent(path: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def export_csv(df: pd.DataFrame, path: Any) -> None:
    _ensure_parent(path)
    df.to_csv(path, index=False)


def export_excel(df: pd.DataFrame, path: Any) -> None:
    _ensure_parent(path)
    df.to_excel(path, index=False)
