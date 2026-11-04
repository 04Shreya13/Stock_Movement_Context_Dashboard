# DSO 576 Module 6 — Project Data Cleaning

**Project:** Spotify Financial Performance Data Cleaning  
**Student:** Haley Wong  
**GitHub branch:** branch_haley  
**Branch URL:** (https://github.com/04Shreya13/Stock_Movement_Context_Dashboard/tree/branch_haley)

## 14-item checklist

### 1. State the project vision and question — Done

**Evidence:** The vision is a financial analyst agent that uses Spotify's public financial statements to describe performance. The business question is: how have revenue growth, gross margin, operating profitability, net profitability, operating cash flow, and liquidity changed over time? The main comparisons are year-over-year revenue growth, gross margin, and operating margin. See `README.md` and `data/processed/spotify_year_summary.csv`.

### 2. Define one row — Done

**Evidence:** One cleaned row is one financial metric for one calendar year in EUR. `record_id = calendar_year + metric + unit` is unique. The script found 61 rows and 61 unique record IDs. See `reports/cleaning_audit.json`.

### 3. Preserve the source — Done

**Evidence:** Source: SEC Company Facts for Spotify Technology S.A. (CIK 1639920), downloaded 2026-10-03 from `https://data.sec.gov/api/xbrl/companyfacts/CIK0001639920.json`. The dated raw file is unchanged at `data/raw/spotify_companyfacts_2026-10-03.json`; SHA-256 is `cc022970e9b216233a25843b42f2a8a528dd92feb38500f9759c0109fccf84e0`. The source is loaded as JSON by `scripts/clean_spotify_financials.py`.

### 4. Inspect columns and types — Done

**Evidence:** Raw values are nested JSON. The script parses `period_start`, `period_end`, and `filed_date` as ISO dates for validation; confirms values are numeric; converts the calendar year to integer; and writes numeric `value_eur`. There were 0 failed date or numeric conversions. See `tests/test_cleaning.py::test_types_dates_and_units` and `reports/cleaning_audit.json`.

### 5. Standardize text — Done

**Evidence:** XBRL concepts such as `ProfitLossFromOperatingActivities` become stable snake_case labels such as `operating_profit_loss`. Unit and form text are stripped and uppercased (`EUR`, `20-F`), and accession numbers remain strings so punctuation/leading characters are preserved. See `METRICS` and `flatten_selected_facts()` in the cleaning script.

### 6. Investigate duplicates — Done

**Evidence:** Among 152 selected source observations, there were 0 exact duplicate rows. There were 91 extra observations with repeated metric/year/unit business keys because annual filings repeat comparative years. For each repeated key, the script retained the latest filing and kept all decisions in `reports/deduplication_audit.csv`. This produced 61 unique rows. No repeated group had conflicting values.

### 7. Handle missing data — Done

**Evidence:** Before cleaning, 32 of 152 selected facts lacked `period_start` and 91 lacked `frame`; required end date, value, accession, and filed date had 0 missing values. After deduplication, 11 `period_start` values remain blank, all for `cash_and_cash_equivalents`. This is intentional because balance-sheet cash is an instant fact measured at year-end. `frame` is not carried into the analytic output because it is nonessential and systematically absent in comparative contexts. Every analytic value is present.

### 8. Check suspicious values — Done

**Evidence:** All dates are valid ISO dates; all filing dates occur after period end; duration facts span 365 or 366 days; all revenue is positive; and gross profit is between zero and revenue. Negative profit values were retained because they represent real losses. The unusually low 2022 operating cash flow (€46 million) was checked and retained. See `test_financial_relationships_and_suspicious_values` and the record checks.

### 9. Verify merges — Not applicable

**Explanation:** No tables were merged. The input is one Company Facts document. The year summary pivots the cleaned long table by its already-validated year/metric key; each 2016–2025 year has all six metrics and `metric_value_count = 6`, so the pivot adds no records.

### 10. Reconcile changes — Done

**Evidence:** 152 selected observations → 61 cleaned rows. The difference is exactly 91 older repeated filing contexts removed by the latest-filing rule. No values were imputed and no unique annual facts were dropped. Important totals are not summed across filing contexts because doing so would triple-count comparative facts. `reports/deduplication_audit.csv` accounts for every selected row.

### 11. Check calculations — Done

**Evidence:** For 2016–2025, every annual metric has 10 nonmissing values (60 values total); the separate 2015 record is an opening cash balance. Gross margin denominator is revenue and uses 10 records; operating margin denominator is revenue and uses 10 records; revenue YoY uses 9 year pairs because 2016 has no prior-year revenue in the analysis table. Missing values are never treated as zero. Missing group keys are rejected by the required concept and date checks. See `create_year_summary()` and `spotify_year_summary.csv`.

### 12. Verify individual records — Done

**Evidence:** Five expectations were written in `create_record_checks()` and then compared with output. All 5 matched. The table below shows original/expected/actual values; full provenance is in `reports/five_record_checks.csv`.

| Record | Original | Expected | Actual | Result |
|---|---:|---:|---:|---|
| 2017 net profit/loss | -1,235,000,000 | -1,235,000,000 | -1,235,000,000 | Match |
| 2021 operating profit/loss | 94,000,000 | 94,000,000 | 94,000,000 | Match |
| 2022 operating cash flow | 46,000,000 | 46,000,000 | 46,000,000 | Match |
| 2024 cash and equivalents | 4,781,000,000 | 4,781,000,000 | 4,781,000,000 | Match |
| 2025 revenue | 17,186,000,000 | 17,186,000,000 | 17,186,000,000 | Match |

### 13. Test reproducibility — Done

**Evidence:** From the project directory, run `python -m pip install -r requirements.txt`, `python scripts/clean_spotify_financials.py`, and `python -m unittest discover -s tests -v`. A clean run recreated all outputs and all 5 tests passed. `haley.ipynb` provides the same restart-and-run workflow.

### 14. Document remaining limitations — Done

**Evidence:** Company-reported XBRL is not an independent accounting audit. The selected six metrics exclude segment, subscriber, market-price, and acquisition-target data. Historical results describe financial capacity but cannot alone recommend an M&A decision. Latest-filing selection could incorporate a later restatement; therefore accession and filing date are retained, and all contexts remain in the audit. The next phase needs defined M&A targets, valuation assumptions, and risk criteria.

## Cleaning decision log

| Rule | Reason | Check |
|---|---|---|
| Select six decision-relevant IFRS concepts | Keeps the dataset aligned with growth, profitability, cash generation, and liquidity | All six concepts exist; 61 final facts |
| Keep FY Form 20-F facts in EUR ending December 31 | Makes years and units comparable | All final rows are `20-F`/`FY`/`EUR`; 0 invalid dates |
| Require 365/366 days for duration facts | Prevents quarterly or year-to-date values from being mislabeled annual | Automated duration validation passes |
| Allow blank start only for instant cash facts | A balance-sheet fact is measured on a date, not over a duration | All 11 remaining blanks are cash instant facts |
| Keep latest filing for each metric/year/unit | Later filings are the best available presentation and repeated comparisons must not be double-counted | 91 older contexts removed; 0 value conflicts |
| Preserve negative profit values | A loss is meaningful data, not an error | Negative cases remain and pass record checks |
| Do not impute financial values | Invented values would distort margins and trends | 0 missing analytic values; no fill operation exists |
| Use explicit formulas and denominators | Makes derived metrics auditable | 10 gross margins, 10 operating margins, 9 YoY growth rates |

## How I checked a Codex suggestion

Codex suggested deduplicating repeated annual facts by retaining the latest filing date. I did not accept that only from the suggestion. I inspected `reports/deduplication_audit.csv`, confirmed that the 91 removed observations were older filing contexts for the same metric/year/unit, and checked `groups_with_conflicting_values_across_filings` in the audit report. It was 0. I also ran the uniqueness/count test, which confirmed 152 source observations minus 91 older contexts equals 61 unique output rows. **Before submitting, the student should personally repeat this check and rewrite this paragraph in their own words.**

## Sample selection

`data/sample/spotify_clean_sample_50.csv` contains the most recent 50 cleaned rows, sorted reproducibly by year and metric. This emphasizes decision-relevant recent performance while still including difficult cases: negative profit/loss, the 2022 low operating cash flow, instant cash records with blank start dates, and repeated-context selections visible through accession numbers. The full 61-row cleaned file and 152-row audit remain available for complete verification.
