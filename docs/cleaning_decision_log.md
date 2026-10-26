# Cleaning Decision Log: Stock Movement Context Dashboard

**Student:** Shreya · **Branch:** `cleaning-shreya`
**Status:** Phase 1. Rules written *before* any cleaning code was applied. Evidence is in `data_cleaning.ipynb`, Phase 1 section.

---

## 1. Source (checklist #3)

| Item | Value |
|------|-------|
| Dataset | [TheFinAI/Herculean](https://huggingface.co/datasets/TheFinAI/Herculean) (CC-BY-4.0) |
| Dataset version (HF commit SHA) | `52d3ecb97e490a2392717935402cde283e8fa36e` (last modified 2026-05-04) |
| Download date | 2026-10-04 |
| Files used | `data/prices.parquet`, `data/news.parquet`, `data/filings.parquet` from the HF repo, saved unchanged in `data/raw/` |

| File | Bytes | SHA-256 (matches the HF LFS hash) |
|------|-------|-----------------------------------|
| prices.parquet | 67,349 | `736c124db22e976dbf4ec1dd65e5a983497e5890e7999f7925b343dee5c965d5` |
| news.parquet | 5,216,446 | `1fd109796eada02af37a15178cc150ec252e7c02bc440c3f76641eb8fab6da25` |
| filings.parquet | 600,603 | `822a854865651e042c9d64288785efa0f2c0fecdec2a16016ff3c2e7a5601299` |

The raw files are never written to. The notebook recomputes these hashes on every run to show they are unchanged.

---

## 2. One row and unique key (checklist #2)

| Table | One row = | Unique key | Verified |
|-------|-----------|------------|----------|
| prices | one symbol on one trading day | `(symbol, date)` | 2,656 rows = 8 symbols × 332 trading days, identical date set for every symbol, 0 duplicate keys |
| news | one symbol on one calendar day | `(symbol, date)` | 3,888 rows = 8 × 486 calendar days (2024-12-01 → 2026-03-31), no gaps, 0 duplicate keys |
| filings | one 10-K / 10-Q filing | `(symbol, date, document_type)` | 73 rows (ADBE 10, others 9), 0 duplicate keys |

`id` in each table is a surrogate key running 1…n with no repeats. It carries no business meaning.

---

## 3. What inspection found (raw data)

| Area | Finding |
|------|---------|
| Types | Parquet stores `date` as `date32`, but pandas loads it as **`object`** (Python `date`). All other types are correct (float prices, int64 volume, string text). |
| Missing | **0 nulls** in every column of all three tables. 0 empty strings. |
| Duplicates | 0 exact duplicate rows, 0 duplicate rows ignoring `id`, 0 repeated `id`s, 0 repeated keys. |
| Symbols | Exactly the 8 expected tickers, no stray whitespace or case variants. |
| Prices | 0 rows with low > high, open/close outside [low, high], non-positive prices, or volume ≤ 0. No splits (adj_close/close ratio never jumps > 2%). Market closures such as 2025-01-09 and holidays are correctly absent. |
| Extreme ranges | Largest daily ranges are TSLA 2025-04-09 (18.7%), TSLA 2025-06-05 (18.0%), and TSLA and NVDA on 2025-04-07 and 2025-04-09. These are real market events (April 2025 tariff volatility), not errors. |
| News text | 5 of 3,888 highlights are under 300 characters and are broken or "no content" LLM output, e.g. ADBE 2025-01-26 = `"The article also includes"`. 1,112 news rows fall on weekends (1,232 on non-trading days). |
| Filing text | All 73 `mda_content` and 68 of 73 `risk_content` values contain HTML entities (`&#160;`, `&#8217;`, `&#8226;`…). All 73 have leading or trailing whitespace. |
| Filing risk sections | 10 of the 10-Q `risk_content` values are under 2,000 characters and only refer back to the annual 10-K. 7 risk texts repeat earlier ones word-for-word, spread across 11 rows (TSLA, GOOGL, AMZN 10-Qs). |
| Filing `date` meaning | It is the **filing date**, not the period end. Evidence: AAPL 10-Ks are dated 2024-11-01 and 2025-10-31 (fiscal year ends late September), MSFT 10-Ks are dated 2024-07-30 and 2025-07-30 (fiscal year ends June 30), and NVDA 10-Ks are dated in late February (fiscal year ends late January). An as-of join on filing date therefore has no look-ahead. |
| Coverage | 32 of 73 filings are dated before the first price date (2024-12-02). |

---

## 4. Cleaning rules (rule · reason · check)

| # | Rule | Reason | Check |
|---|------|--------|-------|
| R1 | Convert `date` to `datetime64` in all three tables (`pd.to_datetime`, `errors="coerce"`). | Pandas reads it as `object`, which breaks `.dt` accessors and `merge_asof`, and tables must share one date type to join. | Failed conversions (NaT) = 0. Min and max dates unchanged. dtype is `datetime64` in all three tables. |
| R2 | Validate `symbol` against the 8-ticker set. Strip and uppercase *only if* needed (no change expected). | Ticker is the join key in every table. | Count of values changed = 0. Set of symbols = the 8 tickers. |
| R3 | Validate `document_type` ∈ {`10-K`, `10-Q`}. | Labels the SEC panel and the "latest 10-K" lookup. | 0 values outside the set. Counts 22 × 10-K, 51 × 10-Q. |
| R4 | Filings `mda_content` and `risk_content`: `html.unescape`, then strip outer whitespace. **No other edits** (no lowercasing, no rewording). | Analysts read this text. Entities like `&#8217;` display as noise. | Rows changed = 73 (mda) and 73 (risk). Rows still containing `&#…;` after cleaning = 0. Show before and after for one record. |
| R5 | News `highlights`: leave text **unchanged**. Add a flag `highlights_low_info = len < 300`. | The text is already clean (no entities or whitespace issues). The 5 broken summaries are real source rows, so keep them and warn the analyst rather than delete them. | Flag count = 5. Rows unchanged = 3,888. |
| R6 | Filings: add a flag `risk_refers_to_10k = len(risk_content) < 2,000` (after R4). | These 10-Q risk sections just point to the 10-K. The dashboard should then also show the latest 10-K risk factors. | Flag count = 10 (all 10-Q). |
| R7 | Keep all rows. No deduplication. | There are no duplicate rows or keys. Repeated `risk_content` is legitimately copied disclosure text, not a duplicate record. | Row counts in = out: 2,656 / 3,888 / 73. |
| R8 | Keep all price rows, including extreme ranges. Derive `daily_range_pct = (high − low) / close`. | Extreme days are exactly what the dashboard looks for. "Unusual" ≠ wrong. Same-day ratio, so split adjustment is irrelevant. | 2,656 non-null values. Spot-check TSLA 2025-04-09 by hand. |
| R9 | No imputation. | There are no missing values. If any appear in future data, rows with null high, low or close are excluded from range calculations but kept in the table. | Nulls before = after = 0 per column. |
| R10 | Keep filings dated before 2024-12-02. | The earliest trading days need a "most recent filing" from before the price window. | 32 such filings kept. Every trading day has a prior filing. |
| R11 | Keep weekend and holiday news rows. | The news panel uses a calendar-day window (D−7 … D), so Monday flags rely on weekend news. | 1,112 weekend rows kept. |
| R12 | Flag a day when `daily_range_pct` ≥ its symbol's 95th percentile. Add `co_flag_count` = companies flagged on the same date. | This is the project's definition of an unusually wide day. Per symbol, because TSLA's normal range (median 3.8%) is about 2.4× MSFT's (1.6%). `co_flag_count` is a partial check for market-wide moves. | 17 flagged per symbol, 136 total (Phase 3 §3.4). |
| R13 | Build `price_context`: prices joined to same-day news (`one_to_one`), latest filing (as-of, same day allowed), and latest 10-K (as-of). Carry ids only, not text. | One row per trading day feeds the dashboard. Text stays in its source table, so it isn't copied 2,656 times. | 2,656 rows in and out, 0 unmatched, 0 duplicate keys, no look-ahead (Phase 3 §3.2). |

**Decision (confirmed 2026-10-04): same-day filings are included.** The as-of join uses `allow_exact_matches=True`, so a filing dated on the flagged day itself counts as that day's latest filing. Many filings come out *after* the close and may not have affected that day's price, so the joined table carries a `filed_same_day` flag and the dashboard shows a "filed same day" note. The join is built and verified in Phase 3 (checklist #9).

---

## 5. Record checks: chosen and expected results written *before* cleaning (checklist #12)

> 📌 **Note:** the five record checks are *completed* in Phase 3 (Step 16), which compares expected and actual results. They are **selected and their expected results written here in Phase 1**, before any cleaning code exists, as checklist #12 requires ("write the expected result and reason before checking the output"). The "Actual" and "Match" columns were filled in Phase 3 from the cleaned outputs (`data_cleaning.ipynb` §3.5). All 5 match.

| # | Record (why it's difficult) | Original value (raw) | Expected result + reason | Actual | Match |
|---|------------------------------|----------------------|--------------------------|--------|-------|
| 1 | **prices** id 2412 · TSLA 2025-04-09: largest range in the dataset | high 274.690002, low 223.880005, close 272.200012 | `daily_range_pct` = (274.690002 − 223.880005) / 272.200012 ≈ **0.18666**. Row kept, not treated as an error (R8). | `daily_range_pct` = 0.18666, row kept, `is_flagged = True` | ✅ |
| 2 | **prices** id 1 · AAPL 2024-12-02: first trading day, so its filing must come from before the price window | date `2024-12-02`, no filing in the price window yet | Latest filing = **AAPL 10-K filed 2024-11-01 (filings id 4)** from the as-of join (R10). | Latest filing = id 4 (10-K, 2024-11-01) | ✅ |
| 3 | **prices** id 2050 · NVDA 2025-02-26: filing on the same day | NVDA 10-K (filings id 60) dated 2025-02-26 | With `allow_exact_matches=True`, latest filing = **id 60 (10-K, same day)**, not the 2024-11-20 10-Q, and `filed_same_day = True`. | Latest filing = id 60 (10-K), `filed_same_day = True` | ✅ |
| 4 | **news** id 543 · ADBE 2025-01-26 (Sunday): broken LLM summary | highlights = `"The article also includes"` (25 chars) | Text **unchanged**, `highlights_low_info = True`, row kept. Appears in the D−7 window for ADBE 2025-01-27 (Monday). | Text unchanged, `highlights_low_info = True`, in the ADBE 2025-01-27 window | ✅ |
| 5 | **filings** id 1 · AAPL 2024-02-01 10-Q: HTML entity and leading space | mda_content starts `" Item 2. Management&#8217;s Discussion…"` | Starts `"Item 2. Management’s Discussion…"`: leading space removed and `&#8217;` → `’` (R4). | Starts `"Item 2. Management’s Discussion…"` | ✅ |

---

## 6. Remaining limitations (checklist #14)

| # | Issue | How it could affect conclusions | Information still needed |
|---|-------|---------------------------------|--------------------------|
| L1 | **No market or sector benchmark.** The data has only these 8 stocks, with no index (e.g., S&P 500, Nasdaq-100) or sector ETF. | Market-wide days can only be estimated with `co_flag_count`. 47 of 136 flagged days have 5 or more companies flagged together (e.g., all 8 on 2025-04-07 to 04-10). A day flagged for only one company could still be sector-driven (e.g., semiconductors). | Daily index and sector ETF prices for the same dates. |
| L2 | **News is LLM-written summaries, not source articles.** 5 summaries are broken, and one of them falls on a flagged day (META 2024-12-18). | Highlights may omit, misstate, or invent events. The analyst cannot check them against the original reporting. A broken summary leaves that day with no news context. | Original article links or headlines with timestamps. |
| L3 | **News and filing dates have no time of day.** | We can't tell whether news or a filing came before or after the market moved. 41 trading days have a filing dated the same day (`filed_same_day`), and many filings are released after the close. | Publication and EDGAR acceptance timestamps. |
| L4 | **10-Q risk sections are often reference-only.** 10 of the 10-Q `risk_content` values only point back to the annual 10-K. | The "latest filing" panel can show almost no risk information. Mitigated by `latest_10k_id`, though the 10-K may be up to a year old. | None. Handled in the dashboard by showing the latest 10-K's risk factors. |
| L5 | **The flag threshold is relative and fixed.** Top 5% per company over the full 16-month window. | Every company gets exactly 17 flags, even if one company was calm overall. The threshold uses the full period, including future days, which is acceptable for a review tool but not for real-time alerting. Different thresholds (e.g., top 2% or a rolling window) would flag different days. | Analyst feedback on whether 17 per company is a useful workload. |
| L6 | **Intraday range ignores overnight gaps.** `(high − low) / close` measures movement within the day. | A stock that gaps up 10% at the open and then trades flat has a small range and is not flagged. | Possibly add the close-to-close or open-vs-previous-close change as a second measure (team decision). |
| L7 | **Short, fixed period and 8 large-cap stocks.** | Findings describe this sample (Dec 2024 – Mar 2026), not other stocks or periods. | Not needed for this project's scope. |
