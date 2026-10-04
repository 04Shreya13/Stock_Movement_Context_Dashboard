# Spotify Financial Performance Data Cleaning

This individual DSO 576 submission cleans Spotify Technology S.A. annual financial facts for a financial-analysis agent. The business question is: **How have Spotify's revenue growth, gross margin, operating profitability, net profitability, operating cash flow, and liquidity changed over time?**

## Submission identity

- Student: **Haley Wong**
- GitHub branch: **branch_haley**
- Branch URL: **(https://github.com/04Shreya13/Stock_Movement_Context_Dashboard/tree/branch_haley)**

These fields must also be completed in `reports/module_6_submission.pdf` before submission. This folder is not currently inside a Git repository, so they could not be inferred.

## Source and version

- Entity: Spotify Technology S.A., CIK 1639920
- Raw source: [SEC Company Facts API](https://data.sec.gov/api/xbrl/companyfacts/CIK0001639920.json), a machine-readable representation of the SEC filings linked from [Spotify Investor Relations](https://investors.spotify.com/financials/default.aspx)
- Downloaded: 2026-10-03 (America/Los_Angeles)
- Preserved file: `data/raw/spotify_companyfacts_2026-10-03.json`
- SHA-256: `cc022970e9b216233a25843b42f2a8a528dd92feb38500f9759c0109fccf84e0`

The raw JSON is read-only input and is never modified by the cleaning script. To refresh it as a new version, download the API response under a new dated filename and pass it with `--input`.

## What one row means

In the primary cleaned file, one row represents one Spotify financial metric for one calendar year in EUR. `record_id` (`calendar_year` + `metric` + `unit`) uniquely identifies a row. Repeated XBRL filing contexts are retained in the audit file; the cleaned result uses the most recently filed observation for each business key.

## Reproduce from the raw file

Python 3.11+ is recommended. From this directory:

```powershell
python -m pip install -r requirements.txt
python scripts/clean_spotify_financials.py
python -m unittest discover -s tests -v
python scripts/build_submission_pdf.py
```

Or open `haley.ipynb`, choose the project Python environment, and use **Restart Kernel and Run All Cells**. The cleaner itself uses only the Python standard library. ReportLab is used only to create the submission PDF.

## Expected outputs

- `data/interim/selected_facts_all_filings.csv`: 152 selected observations, including repeated filing contexts.
- `data/processed/spotify_annual_financials_clean.csv`: 61 unique metric/year rows covering 2015–2025 (2015 contains only the opening cash balance).
- `data/processed/spotify_year_summary.csv`: 10 complete annual rows for 2016–2025 and derived margins/growth.
- `data/sample/spotify_clean_sample_50.csv`: 50-row instructor review sample emphasizing recent years while retaining difficult loss and low-cash-flow records.
- `reports/cleaning_audit.json`: counts, missingness, conversion checks, source hash, and rules.
- `reports/deduplication_audit.csv`: every retained/removed filing context and the decision.
- `reports/five_record_checks.csv`: original, expected, and actual results for five predeclared checks.
- `reports/module_6_submission.pdf`: Gradescope-ready narrative after personal fields are filled.

## Important limitations

The dataset is company-reported IFRS data, not independently recalculated accounting data. The six selected metrics support historical financial-performance analysis but do not by themselves justify a merger or acquisition. XBRL comparative facts repeat across filings; this project keeps the newest filing, while the audit file preserves every older context. No conflicting values were observed for the same selected metric/year/unit in this version, but the rule matters for future amended filings.
