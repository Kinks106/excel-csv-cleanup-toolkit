"""Command-line interface for the cleanup toolkit.

Example:
    python -m cleanup_tool.cli \
        --input data/sample_input/sample_sales.csv \
        --output data/sample_output/cleaned_sales.csv \
        --report data/sample_output/cleaning_report.json \
        --config config/cleaning_rules.example.json
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from . import cleaners, exporters, readers, reporting, validators
from .config import CleaningConfig

log = logging.getLogger("cleanup_tool")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cleanup-tool",
        description="Clean, validate and report on messy CSV/Excel files.",
    )
    p.add_argument("--input", required=True, help="Path to the input CSV/TSV/Excel file.")
    p.add_argument("--output", required=True, help="Path for the cleaned CSV output.")
    p.add_argument("--report", required=True, help="Path for the JSON processing report.")
    p.add_argument("--config", default=None, help="Optional JSON config of cleaning rules.")
    p.add_argument("--excel-output", default=None, help="Optional path to also write .xlsx.")
    p.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO).",
    )
    return p


def run_pipeline(
    input_path, output_path, report_path, config: CleaningConfig, excel_output: Optional[str] = None
):
    """Run the full clean -> validate -> export -> report pipeline.

    Returns ``(cleaned_df, report_dict, validation_result)``.
    """
    # Never overwrite the raw input.
    if Path(output_path).resolve() == Path(input_path).resolve():
        raise ValueError("Output path must differ from the input path; refusing to overwrite raw input.")

    df = readers.read_table(input_path)
    rows_in = len(df)
    columns_in = list(df.columns)
    steps: dict = {}

    if config.normalize_columns:
        df, info = cleaners.normalize_column_names(df)
        steps["column_rename"] = info["renamed"]

    if config.drop_empty_rows:
        df, info = cleaners.remove_empty_rows(df)
        steps["empty_rows_removed"] = info["empty_rows_removed"]

    if config.text_case:
        df, info = cleaners.normalize_text_case(df, config.text_case)
        steps["text_case"] = info["text_case_applied"]

    if config.date_columns:
        df, info = cleaners.parse_dates(df, config.date_columns)
        steps["dates"] = info["dates_parsed"]

    df, info = cleaners.handle_missing_values(df, config.missing_value_rules, config.default_missing)
    steps["missing"] = info["missing_handling"]
    steps["rows_dropped_for_missing"] = info["rows_dropped_for_missing"]

    if config.drop_duplicates:
        df, info = cleaners.remove_duplicates(df, config.duplicate_subset)
        steps["duplicates_removed"] = info["duplicates_removed"]
        steps["duplicate_subset"] = info["subset"]

    vr = validators.validate(df, config.required_columns, config.column_types)
    rows_out = len(df)
    columns_out = list(df.columns)

    report = reporting.build_report(
        input_path, rows_in, columns_in, steps, rows_out, columns_out, vr.to_dict()
    )

    exporters.export_csv(df, output_path)
    if excel_output:
        exporters.export_excel(df, excel_output)
    reporting.write_report(report, report_path)

    return df, report, vr


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=args.log_level, format="%(levelname)s %(name)s: %(message)s")

    try:
        config = CleaningConfig.from_file(args.config) if args.config else CleaningConfig()
    except (ValueError, FileNotFoundError, OSError) as exc:
        log.error("Could not load config: %s", exc)
        return 2

    try:
        _, report, vr = run_pipeline(
            args.input, args.output, args.report, config, args.excel_output
        )
    except FileNotFoundError as exc:
        log.error("%s", exc)
        return 2
    except ValueError as exc:
        log.error("%s", exc)
        return 2
    except Exception as exc:  # pragma: no cover - last-resort guard
        log.exception("Unexpected failure: %s", exc)
        return 1

    print(reporting.summarize_text(report))
    log.info("Cleaned file -> %s", args.output)
    log.info("Report       -> %s", args.report)

    if not vr.ok:
        log.warning("Validation failed: %s", vr.errors)
        return 3  # cleaned output is still written for inspection
    return 0


if __name__ == "__main__":
    sys.exit(main())
