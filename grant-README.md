# Stock Movement Context Dashboard: Data Cleaning

This project inspects and prepares the prices, news, and filings tables for the Stock Movement Context Dashboard. The workflow preserves the supplied source data and writes reproducible outputs under `outputs/`.

## Data source and version

- **Dataset:** [TheFinAI/Herculean on Hugging Face](https://huggingface.co/datasets/TheFinAI/Herculean)
- **Tables used:** `prices.parquet`, `news.parquet`, and `filings.parquet`
- **Version/revision or download date:** Not recorded in the project materials that accompanied these files. The generated `outputs/cleaning_report.json` records a SHA-256 hash for each local input file so this exact copy can be identified.
- **Local input layout:** Place the three original files in the `data/` directory. The script never overwrites them.

## Cleaning decisions

- Convert each `date` column to a datetime type and count conversion failures. Invalid dates, if any, are kept as `NaT` and reported for review rather than silently dropped.
- Preserve row counts, IDs, symbols, and all text. Do not fill missing values or remove duplicates automatically; report those conditions for review.
- Keep news records on weekends and holidays. They are calendar-day records and can provide context for nearby trading days.
- Validate price constraints, candidate keys, same-day news coverage, the previous-seven-calendar-day news window, and latest filing selection as of each price date.
- Calculate both raw daily range (`high - low`) and normalized range (`(high - low) / close`). No movement flagging threshold is applied because the project description presents more than one possible rule; choose the threshold before building flags.
- Filing text is preserved exactly, including leading/trailing whitespace. Any decision to trim that whitespace remains for review.

## Requirements and run instructions

Use Python 3.10 or later. From the project root, install the pinned dependencies and run the script:

```bash
python -m pip install -r requirements.txt
python cleaning_scripts.py
```

The notebook walkthrough is `cleaning_notebook.ipynb`. Open it from the project root and run all cells; it runs the same script and displays the checks and validation results. The code uses paths relative to the project files, so the original inputs must be available in `data/`.

## Expected output files

Running `cleaning_scripts.py` creates or replaces these files in `outputs/`:

- `prices_cleaned.parquet`, `news_cleaned.parquet`, `filings_cleaned.parquet` — source rows with dates converted to datetime; current run retains all rows.
- `price_metrics.csv` — raw and normalized daily range calculations; no flags are assigned.
- `news_window_counts.csv` — news record count for each price date’s same-symbol, inclusive prior-seven-calendar-day window.
- `filing_lookup.csv` — latest same-symbol filing on or before each price date.
- `record_checks.csv` — five expected-versus-actual record checks.
- `data_sample.csv` and `data_sample.parquet` — the same 48 rows across the three tables, including difficult cases; selection reasons are included as columns.
- `cleaning_report.json` — input hashes, type/missingness/duplicate/value checks, reconciliation, cross-table checks, calculation summary, record-check status, and sample details.

## Current inspection results

The current run found 2,656 price rows, 3,888 news rows, and 73 filing rows. All three date columns converted with zero failures. No rows were removed; the same number of rows appears in each cleaned output. All five record checks passed. The news lookup matched all 2,656 price dates to same-day news and retained 1,232 news dates without a same-day price. All 2,656 price dates found a prior filing and at least one news item in the defined context window.

## Assignment submission details

Fill these in after pushing to your individual assignment branch:

- **Branch name:** `[fill in]`
- **Branch URL:** `[fill in]`
- **Commit ID:** `[fill in]`
