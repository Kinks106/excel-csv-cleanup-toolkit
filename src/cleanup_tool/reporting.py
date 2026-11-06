"""Build and render the processing report."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def build_report(
    input_path: Any,
    rows_in: int,
    columns_in: list,
    steps: dict,
    rows_out: int,
    columns_out: list,
    validation: dict,
    rejected: int = 0,
) -> dict:
    removed = {
        "empty_rows": int(steps.get("empty_rows_removed", 0)),
        "missing_dropped": int(steps.get("rows_dropped_for_missing", 0)),
        "duplicates": int(steps.get("duplicates_removed", 0)),
    }
    total_removed = sum(removed.values())
    balanced = rows_in == rows_out + total_removed + rejected
    return {
        "tool": "excel-csv-cleanup-toolkit",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_file": str(input_path),
        "rows_in": rows_in,
        "columns_in": columns_in,
        "steps": steps,
        "rows_removed": removed,
        "rows_rejected": rejected,
        "rows_out": rows_out,
        "columns_out": columns_out,
        "reconciliation": {
            "formula": "rows_in == rows_out + removed + rejected",
            "rows_in": rows_in,
            "rows_out": rows_out,
            "removed_total": total_removed,
            "rejected": rejected,
            "balanced": bool(balanced),
        },
        "validation": validation,
    }


def write_report(report: dict, path: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")


def summarize_text(report: dict) -> str:
    r = report
    lines = [
        "Cleanup summary",
        "===============",
        f"Input           : {r['input_file']}",
        f"Rows in         : {r['rows_in']}",
        f"Rows out        : {r['rows_out']}",
        f"Removed         : empty={r['rows_removed']['empty_rows']} "
        f"missing={r['rows_removed']['missing_dropped']} "
        f"duplicates={r['rows_removed']['duplicates']}",
        f"Reconciles      : {r['reconciliation']['balanced']}",
        f"Validation OK   : {r['validation']['ok']}",
    ]
    if r["validation"]["errors"]:
        lines.append(f"Validation errs : {r['validation']['errors']}")
    return "\n".join(lines)
