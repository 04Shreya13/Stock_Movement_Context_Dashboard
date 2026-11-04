# My Module 9 audit

## Context

- **Name:** Haley Wong
- **Team app and version or commit checked:** Stock Movement Context Dashboard,
  commit `8ace87fa46a1ab58d7d9ed216f49e7513c29f33b`, including
  `SHARE_DASHBOARD.zip`, checked on 2026-10-22.
- **Intended user and decision:** An investor-relations analyst uses the app to
  shortlist unusually wide stock-price movements and decide which dates deserve
  follow-up research. The app supplies context; it does not claim that a news
  item or filing caused a movement.

## 1. Feature audit

- **Feature and intended behavior:** The analyst selects a stock, reviews its
  flagged trading days, and selects one row to update the selected-day metrics,
  eight-stock comparison, nearby news, and latest eligible SEC filing. The build
  specification says flagged days should be sorted by daily range descending,
  with the earliest date breaking a tie.
- **Inputs and steps to reproduce:** I checked the app archive at the commit
  above. From the repository root, run
  `uv run --frozen python scripts/audit_haley.py`. To reproduce manually, open
  `SHARE_DASHBOARD.zip`, compare the imports at the top of `app.py` and
  `dso576_python/data_loader.py` with the archive's file paths, and then follow
  the archive's `README.txt` startup instructions.
- **Expected behavior:** The documented installation command should start the
  dashboard. Choosing AAPL and a flagged row should make the event-context
  panels available.
- **Actual behavior and evidence:** The app cannot start as packaged.
  `app.py` imports `dso576_python.charts`, but the archive places `charts.py` at
  its root instead of at `dso576_python/charts.py`. The packaged
  `data_loader.py` also imports `dso576_python.cleaning`, but `cleaning.py` is
  absent. The reproducible audit script confirms both missing module paths.
  Because imports fail before the interface loads, no user can reach the
  flagged-day table in this artifact.
- **Conclusion and recommended change:** The feature's selection logic exists in
  source code, but the feature is unavailable to its intended user in the
  checked build. I requested **CR-HW-001**: correct the package layout and add a
  fresh-clone startup test that reaches and exercises the flagged-day table.

## 2. Number audit

- **Number audited and its meaning:** The normalized daily range intended to be
  displayed for AAPL on 2025-04-09. It measures how wide that day's intraday
  high-to-low span was relative to its closing price. It is not a daily return,
  does not show direction, and is not evidence of causation.
- **Formula, units, population, and time window:** For one company on one trading
  day, `daily_range_pct = (high - low) / close`. It is a unitless ratio displayed
  as a percentage. A day is flagged when its ratio is at or above that company's
  95th percentile across the full 332-day sample from 2024-12-02 through
  2026-03-31; the threshold is not recalculated for a selected year.
- **Relevant data assumptions:** `high`, `low`, and `close` use the same currency
  and refer to the same stock and trading day. Prices are positive. The canonical
  Parquet files are the team's pinned dataset. I did not independently validate
  those prices against an outside market-data source.
- **Code checked:** `src/dso576_python/cleaning.py`, especially the line computing
  `(high - low) / close` and the lines computing each symbol's 0.95 quantile and
  `>=` flag. I also checked `SHARE_DASHBOARD/app.py`, which formats the stored
  ratio with two percentage decimals. My independent check is
  `scripts/audit_haley.py`.
- **What this code computes, in my own words:** It subtracts the day's low from
  its high to get the dollar trading span, divides that span by the closing
  price to make different price levels more comparable, and flags values in the
  highest five percent of that company's full-sample distribution, including
  values equal to the cutoff.
- **Small test case and expected result:** The AAPL row on 2025-04-09 has high
  `200.61000061`, low `171.88999939`, and close `198.85000610`. Using rounded
  values by hand, `(200.61 - 171.89) / 198.85 = 0.14443`, so I expected the app
  to show `14.44%` after rounding to two percentage decimals.
- **Actual result:** Using the full stored precision, my independent calculation
  was `0.14443047693824218`, or `14.44304769%`. The canonical
  `daily_range_pct` was exactly the same and therefore formats to `14.44%`. The
  independently recomputed AAPL 95th percentile was `0.043258086272`
  (`4.3258%`), and both the recomputation and stored flags contained 17 AAPL
  days.
- **Independent calculation or check:** My audit script loads only the canonical
  tables and directly computes `(high - low) / close`; it does not call the
  dashboard's cleaning or analysis functions. All 332 AAPL values matched the
  stored values within `1e-12`. Recomputing the threshold separately also gave
  17 flags for each of the eight companies.
- **What the evidence establishes and what remains uncertain:** The evidence
  establishes that the stored metric, the AAPL example, and the full-sample flag
  count agree with the documented formula. It does not establish that the source
  prices are externally accurate, and I could not visually confirm the rendered
  `14.44%` because the packaged app cannot start.
- **Recommended change, if any:** No calculation change is requested. Fix
  CR-HW-001, then add an interface-level check confirming that the selected row
  displays `14.44%` and that the label continues to distinguish intraday range
  from return.

## My contribution

- **What I personally checked and concluded:** I selected the flagged-day
  workflow, inspected the packaged import paths, chose a concrete AAPL day,
  checked the metric's meaning and denominator, performed the hand calculation,
  and compared an independent full-table calculation with the canonical values.
  My conclusion is that the metric calculation is consistent, while the audited
  feature is blocked by packaging errors.
- **How AI helped, if used:** AI helped inspect the repository and archive,
  draft the reproducible Python check, run the calculations, and organize this
  report. I reviewed the evidence and am responsible for the audit judgments and
  final wording.
