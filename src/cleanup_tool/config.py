"""Configuration for the cleanup pipeline.

Cleaning behaviour is fully driven by an explicit, inspectable config so that
nothing happens implicitly. A JSON file can override any default.

IMPORTANT: rule keys (text_case, date_columns, missing_value_rules,
required_columns, column_types, duplicate_subset) refer to columns by their
*normalized* names, because column-name normalization runs first in the
pipeline. For example a source header "Order ID" is referenced as "order_id".
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Optional

# Supported missing-value strategies.
MISSING_STRATEGIES = {
    "leave",        # do nothing
    "drop_row",     # drop any row where this column is empty
    "fill_value",   # fill with an explicit "value"
    "fill_mean",    # fill with the column mean (numeric)
    "fill_median",  # fill with the column median (numeric)
    "fill_mode",    # fill with the most frequent value
}

# Supported validation types.
VALID_TYPES = {"int", "integer", "float", "number", "str", "string", "bool", "boolean", "date"}


@dataclass
class CleaningConfig:
    # Column-name normalization (lowercase, strip, non-alphanumerics -> "_").
    normalize_columns: bool = True

    # Drop rows that are entirely empty.
    drop_empty_rows: bool = True

    # Duplicate handling.
    drop_duplicates: bool = True
    duplicate_subset: Optional[list] = None  # None = consider all columns

    # Text-case normalization: {column: "lower" | "upper" | "title"}.
    text_case: dict = field(default_factory=dict)

    # Date parsing: {column: format_string_or_null}. null => let pandas infer.
    date_columns: dict = field(default_factory=dict)

    # Missing-value rules per column: {column: {"strategy": ..., "value": ...}}.
    # Columns not listed fall back to `default_missing`.
    missing_value_rules: dict = field(default_factory=dict)
    default_missing: dict = field(default_factory=lambda: {"strategy": "leave"})

    # Validation (report-only; does not drop rows).
    required_columns: list = field(default_factory=list)
    column_types: dict = field(default_factory=dict)  # {column: type}

    # ---- constructors ---------------------------------------------------

    @classmethod
    def from_file(cls, path: Any) -> "CleaningConfig":
        text = Path(path).read_text(encoding="utf-8")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Config file is not valid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("Config file must contain a JSON object.")
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> "CleaningConfig":
        known = {f.name for f in fields(cls)}
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"Unknown config keys: {sorted(unknown)}")
        cfg = cls(**{k: v for k, v in data.items() if k in known})
        cfg.validate()
        return cfg

    # ---- validation of the config itself --------------------------------

    def validate(self) -> None:
        for col, rule in self.missing_value_rules.items():
            strat = (rule or {}).get("strategy")
            if strat not in MISSING_STRATEGIES:
                raise ValueError(
                    f"Invalid missing-value strategy '{strat}' for column '{col}'. "
                    f"Choose one of {sorted(MISSING_STRATEGIES)}."
                )
            if strat == "fill_value" and "value" not in rule:
                raise ValueError(f"Column '{col}' uses 'fill_value' but has no 'value'.")
        default_strat = (self.default_missing or {}).get("strategy")
        if default_strat not in MISSING_STRATEGIES:
            raise ValueError(
                f"Invalid default_missing strategy '{default_strat}'. "
                f"Choose one of {sorted(MISSING_STRATEGIES)}."
            )
        for col, mode in self.text_case.items():
            if mode not in {"lower", "upper", "title"}:
                raise ValueError(f"Invalid text_case '{mode}' for column '{col}'.")
        for col, typ in self.column_types.items():
            if typ not in VALID_TYPES:
                raise ValueError(
                    f"Invalid column type '{typ}' for column '{col}'. "
                    f"Choose one of {sorted(VALID_TYPES)}."
                )

    def to_dict(self) -> dict:
        return asdict(self)
