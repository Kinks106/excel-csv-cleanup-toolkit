"""Excel & CSV Cleanup and Reporting Toolkit.

A small, deterministic tool that reads messy CSV/Excel files, cleans and
validates them according to explicit, inspectable rules, writes a clean
output file, and emits a machine-readable processing report.

Design principles:
  * The raw input file is never modified or overwritten.
  * Every transformation is driven by an explicit config (no hidden magic).
  * No rows are silently discarded — every removal is counted in the report.
  * Row counts always reconcile: rows_in == rows_out + removed + rejected.
"""

__version__ = "0.1.0"

from .config import CleaningConfig

__all__ = ["CleaningConfig", "__version__"]
