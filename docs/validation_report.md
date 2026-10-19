# Validation Report: Phase 2 Backend on the Canonical Data

**Run on:** 2026-10-18, on Shreya's machine (macOS, Apple Silicon), under `uv` with Python 3.13.15, pandas 3.0.6, NumPy 2.5.3, pyarrow 25.0.1 (the versions locked in `uv.lock`).
**Code:** branch `phase2-integration` (based on `main` at `3231593`), backend files as received in the team's Phase 2 package.
**Data:** the committed canonical files in `data/cleaned/` (team-adopted cleaning; source pinned to Herculean revision `52d3ecb`).

This replaces the package's earlier report, which was written without access to the data and could not run anything on it.

## Update, 2026-10-19 (same machine, same `uv` environment)
After adding the shared `constants.py` module and the full-range period (`period='full'`):
- Tests: **11 of 11 passed** (two new: full-range period, ticker list consistent between `cleaning.py` and `constants.py`).
- `phase2`: **exit 0**, strict validation passed, **16 files** written (the 13 below plus `stock_summary_full.csv`, `indexed_prices_full.csv`, `flagged_days_full.csv`).
- Full range: every company has 17 flagged days; AAPL's largest is 2025-04-09 (range 14.44%, 8 of 8 stocks flagged), the default opening view.
- `cleaning.py` still runs as a standalone script; `data/cleaned/`, `outputs/` and `sample/` remain byte-identical to `main`.

The sections below are the original 2026-10-18 run.

## 1. Tests
`PYTHONPATH=src uv run python -m unittest discover -s tests -v`: **9 of 9 passed.**
The tests use small synthetic fixtures built in memory, so they check logic, not the real data.

## 2. Full-data validation
`PYTHONPATH=src uv run python -m dso576_python.phase2`: **exit 0**, strict validation passed.

| Check | Result |
|-------|--------|
| Row counts | prices 2,656 · news 3,888 · filings 73 · price_context 2,656 |
| Flagged days | 136 in total (17 per company); by year: 2024 → 8, 2025 → 105, 2026 → 23 |
| Exports | 13 files written to `outputs/analysis/` (git-ignored; regenerate with the README command) |

`data_loader.validate_data` checks columns, types, nulls, keys, ticker set, OHLC consistency, the flag rule, co-flag counts, and recomputes every news and filing link.

## 3. Independent checks
Recomputed directly from the cleaned files, not through the function being checked:

| Check | Result |
|-------|--------|
| `year_summary` 2025 for all 8 tickers (period change, last close, trading days, flag count, largest range) | ✅ All match. E.g., AAPL +11.99%, 15 flags; TSLA +18.57%, 15 flags |
| `indexed_prices` starts at 100 for every ticker in 2024, 2025, 2026 | ✅ |
| `filing_context` vs. the stored links in `price_context`, all 2,656 trading days | ✅ 0 mismatches (filing id and same-day flag) |
| Annual 10-K fallback for 10-Qs whose risk section refers to the 10-K | ✅ Applies on 406 trading days; e.g., AAPL 2025-08-01 → 10-K id 4, matching `latest_10k_id` |
| Cleaning record checks via the backend | ✅ NVDA 2025-02-26 → filing 60, filed same day · AAPL 2024-12-02 → filing 4 · news id 543 is in the ADBE 2025-01-27 window |
| `initial_date(2025, AAPL)` | ✅ 2025-04-09 (range 14.44%, 8 of 8 stocks flagged); its news window has 8 rows |
| Inputs left unmodified after calling the functions | ✅ |
| Cleaning with the added `validate_raw()` | ✅ Passes on the raw files; `data/cleaned/`, `outputs/` and `sample/` are byte-identical to `main` |

## 4. Findings to carry into the spec fixes
- **Periods with no flags for some stocks:** 2024 has none for AAPL, ADBE, NVDA; 2026 has none for NVDA, TSLA. Any default "open on AAPL" view in those periods shows no selected event.
- **Running without `PYTHONPATH=src` fails on macOS** (`ImportError`), because Python 3.13 ignores the hidden editable-install `.pth` file. All documented commands set it.

## 5. Not covered here
- The pinned environment in the package (pandas 2.2.3) was not tested; the team uses `uv.lock` instead.
- `scripts/download_source.py` was not run (the dataset is gated; no token was used).
- The dashboard UI (Phase 3), team reconciliation, and the fresh-agent test.
