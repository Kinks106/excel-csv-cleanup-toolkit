# Excel & CSV Cleanup and Reporting Toolkit

A small, reliable command-line tool that turns messy spreadsheets into clean,
validated data — and tells you exactly what it changed.

Small teams often receive CSV/Excel files with inconsistent column names, blank
rows, duplicate records, mixed date formats, and missing values. This tool
standardizes such files and produces a clean output plus a machine-readable
report, so every change is traceable.

## Overview

- **Problem:** manual, error-prone spreadsheet cleanup.
- **Input:** one `.csv` / `.tsv` / `.xlsx` file.
- **Output:** a cleaned CSV (and optional Excel) + a JSON processing report.
- **Intended use:** a repeatable, auditable first-pass cleaner for tabular data.

## Features

- Normalizes column names (`"Order ID"` → `order_id`).
- Removes fully empty rows and reports the count.
- Removes duplicate rows (configurable key columns) and reports how many.
- Handles missing values with **explicit, configurable** rules
  (`fill_value`, `fill_mean`, `fill_median`, `fill_mode`, `drop_row`, `leave`).
- Normalizes text case and parses dates, counting values that fail to parse.
- Validates required columns and column types (**report-only — never drops rows silently**).
- Exports cleaned CSV/Excel and a JSON report whose row counts always reconcile:
  `rows_in == rows_out + removed + rejected`.
- **The raw input file is never modified or overwritten.**

## Tech stack

- Python ≥ 3.9
- pandas, openpyxl
- pytest (dev)

## Repository structure

```text
excel-csv-cleanup-toolkit/
├── README.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── config/
│   └── cleaning_rules.example.json
├── data/
│   ├── sample_input/sample_sales.csv
│   └── sample_output/           # cleaned_sales.csv + cleaning_report.json (generated)
├── src/cleanup_tool/
│   ├── cli.py config.py readers.py cleaners.py validators.py exporters.py reporting.py
└── tests/
    └── test_readers.py test_cleaners.py test_validators.py
```

## Setup

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .            # installs the package + runtime deps
python -m pip install -r requirements-dev.txt   # pytest, for running tests
```

## Run

```bash
python -m cleanup_tool.cli \
  --input data/sample_input/sample_sales.csv \
  --output data/sample_output/cleaned_sales.csv \
  --report data/sample_output/cleaning_report.json \
  --config config/cleaning_rules.example.json
```

(After `pip install -e .` you can also use the `cleanup-tool` command.)

**Exit codes:** `0` success · `2` bad input/config · `3` validation errors
(cleaned output is still written for inspection) · `1` unexpected error.

## Example (sample data)

`data/sample_input/sample_sales.csv` deliberately contains an exact duplicate
row, a case-only duplicate, a fully empty row, missing customer/price/quantity
cells, mixed region capitalization, a slash-format date, and one unparseable
date. Running the command above produces:

- `data/sample_output/cleaned_sales.csv` — standardized columns, filled/validated values.
- `data/sample_output/cleaning_report.json` — counts for every step and a
  reconciliation block proving no rows vanished unaccounted for.

The console prints a short summary (rows in/out, removals, reconciliation, validation).

## Configuration

See `config/cleaning_rules.example.json`. Rule keys refer to columns by their
**normalized** names (normalization runs first). Each missing-value rule is one of:

| strategy | effect |
|---|---|
| `leave` | do nothing |
| `drop_row` | drop rows where this column is empty |
| `fill_value` | fill with an explicit `value` |
| `fill_mean` / `fill_median` | fill numeric gaps with mean/median |
| `fill_mode` | fill with the most frequent value |

## Tests

```bash
pytest
```

## Data and licensing

All sample data is **synthetic** and contains no real personal or client
information. Never commit real client data to this repository.

## Contact

Kinnshuk Bhaduri — https://github.com/Kinks106
