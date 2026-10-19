# Stock Movement Context Dashboard — Phase 2 Build Specification

## 1. Vision and decision
An investor-relations analyst at a large investment firm needs to explain unusual
stock movements before speaking with investors. Bring eight companies' price
histories, nearby news, and available company filings into one workflow. The
analyst decides which movements and disclosures deserve further human review.
This replaces switching between separate charts, news feeds, and filing documents.

Compared with Phase 1, make year comparisons explicit using 2024/2025/2026 tabs;
retain normalized daily range and fixed company-specific thresholds from the
supplied cleaning branch. Remove the sketch's adjustable threshold for the MVP.
The tool supplies historical context, not causal conclusions or forecasts.

| User selects | Dashboard shows | User decides |
|---|---|---|
| Year | Eight-stock indexed comparison and summary table | Which stock deserves investigation |
| Stock | Closing-price chart and ranked flagged dates | Which event to review |
| Flagged date | Range metrics, eight-stock same-date comparison, nearby news, latest eligible filing | Which potential explanations to investigate |
| News section or filing section | Dated stored news/MD&A/risk text and quality labels | Which evidence to verify or discuss |

## 2. Data contract and readiness
Canonical inputs live in `data/cleaned/`: `prices.parquet`, `news.parquet`,
`filings.parquet`, `price_context.parquet`. Loader schemas and executable checks
are in `src/dso576_python/data_loader.py`. Do not use sample CSVs as full data.

Pinned source: TheFinAI/Herculean, revision
`52d3ecb97e490a2392717935402cde283e8fa36e`. Original source checksums are in
`cleaning.py`. Expected dimensions from the supplied branch: 2,656 prices,
3,888 news records, 73 filings, 2,656 context rows. These expectations must pass
on the actual source before submission; they were not reverified on full data here.

| Table | Grain/key | Principal columns |
|---|---|---|
| prices | Company/trading day; symbol + date | id, open, high, low, close, adj_close, volume, daily_range_pct |
| news | Company/calendar day; symbol + date | id, highlights, highlights_low_info |
| filings | Company/filing; symbol + date + document_type | id, document_type, mda_content, risk_content, risk_refers_to_10k |
| price_context | Company/trading day; symbol + date | price_id, prices/range, is_flagged, co_flag_count, news_id, filing_id/date, latest_10k_id/date, quality flags |

Symbols: AAPL/Apple, ADBE/Adobe, AMZN/Amazon, GOOGL/Alphabet, META/Meta,
MSFT/Microsoft, NVDA/Nvidia, TSLA/Tesla. Use this order in initial tables and controls.

Expected price coverage is December 2, 2024–March 31, 2026. Use actual loaded
minimum/maximum dates in coverage labels. 2024 is December only; 2026 is
January–March; 2025 contains the full available year. Do not fabricate missing
months or equate partial-year results with annual returns.

Only Shreya's cleaning branch was supplied. Its decisions are the implemented
baseline, not evidence of agreement by all team members. Complete
`docs/team_reconciliation.md` and include full cleaned files on main before submission.

## 3. Starting view and state
Title: **Stock Movement Context Dashboard**.
Subtitle: "Compare eight stocks, identify unusually wide daily ranges, and review
related news and company filings."

Top-level tabs in order: **2024 | 2025 | 2026**; initially activate **2025**.
Use the same layout in every tab:
1. Coverage banner.
2. Eight-stock relative price chart.
3. Eight-stock summary table.
4. Stock selector and detail chart.
5. Selectable flagged-date table.
6. Selected-date metrics and eight-stock comparison.
7. News and SEC filing context.

On entering another year, reset stock to AAPL and select its largest-range flagged
day in that year; break ties by earliest date. On stock changes, apply the same date
initialization rule. If there are no flags, selected date is None. The required
control for date selection is a single-row selectable table; chart-point selection
is optional and must update the same state.

For Phase 3 use Streamlit with Plotly, adding UI dependencies then. If tab APIs do
not support active-tab state and initialization, implement a three-option segmented
control styled as year tabs. Preserve specified selection behavior; do not rely on
unobserved tab activation. Keep only one active-year detail workflow rendered.

## 4. Year overview
**Coverage banner:** year, actual first/last trading dates, company count, and
partial-year notice. Default overview includes all eight companies.

**Relative price chart:** date on x; adjusted close indexed to 100 on y; eight lines,
legend, horizontal reference at 100. Title: "Relative price performance — first
available trading day = 100". Hover shows company/ticker, date, indexed price and
price change since the first observation in that year. Start each company's
series at 100 separately in each year. Legend toggles affect only this chart.

Use consistent ticker colors across years. Suggested mapping: AAPL #1f77b4,
ADBE #ff7f0e, AMZN #2ca02c, GOOGL #d62728, META #9467bd, MSFT #8c564b,
NVDA #e377c2, TSLA #7f7f7f. Identify lines through legend/hover, not color alone.

**Summary table:** one row per expected ticker, initial ticker-ascending order,
sortable columns: company, ticker, last available close, price change over available
period, flagged trading days, largest normalized daily range, trading days available.
An absent stock must retain a row with unavailable metrics rather than zero returns.
The canonical pinned dataset should normally fail validation if a company is absent.

## 5. Stock and flagged-date details
Dropdown: "Select a stock to investigate"; names include tickers; initial AAPL.
Changing the stock does not filter the all-stock overview.

Detail chart: date on x, unadjusted closing price (USD) on y, line for selected
stock and distinct markers on flagged dates. Hover includes ticker, date, close,
high, low, normalized daily range, flag and co-flag count. Do not interpolate
weekend observations or invent rows.

Flag table contains only selected stock/year flagged records: date, close, high,
low, normalized daily range, co-flag count. Sort range descending, date ascending.
One selected row initializes and updates all context panels.

When no flags exist, display "No flagged trading days for this stock in the
selected year." Retain the price chart; hide selected-event panels. Never borrow
an event from another stock/year.

Selected-date metrics: ticker/company, date, close, high, low, normalized range,
and "X of 8 stocks flagged". Underneath show all eight tickers' normalized ranges
and flag statuses for that date. A missing observation displays unavailable,
never an artificial zero. Co-flags refer to these eight stocks only, not an index.
Explain: "A higher count may suggest shared conditions; it does not establish a
market-wide cause." Do not assign definitive company-specific/market-wide labels.

## 6. News and filing context
**News:** selected ticker, inclusive D−7 through D calendar dates (up to eight
calendar dates). Keep weekends and earlier-year records. Sort newest first,
expand selected-date summary when present, collapse other dates. Show date,
stored highlights, "AI-generated news summary", and "Limited information" when
highlights_low_info is true. No eligible news: "No news summaries are available
for this company in the selected date window."

Do not invent article titles, original links, publication times, or causal
interpretations. Same-day summaries may include information released after market
hours; they are context, not proven information available before the movement.

**Filings:** latest 10-K/10-Q for selected ticker with filing date <= D, even if
from a previous year. Show type/date and expandable MD&A and Risk Factors.
Same-day label: "Filed on selected date; publication time unavailable."
When latest filing is a 10-Q with risk_refers_to_10k true, retain its text and
add the latest eligible 10-K risk text, clearly labeled with annual filing date.
No filing/annual fallback: explicit unavailable message. Do not show future
filings or confuse filing date with fiscal period end. Same-date filing ambiguity
must fail validation and be resolved in cleaning, not silently choose a document.
Stored filing content consists of excerpts, not complete SEC documents.

## 7. Metrics and filter semantics
All backend percentage-like results are decimal ratios; format as percent once
in the interface. Example: 0.05 displays as 5.00%, not 0.05% or 500%.

| Metric/question | Source and calculation | Filters |
|---|---|---|
| Relative price path | prices.adj_close / first adj_close × 100 | Per ticker, selected year, date ascending |
| Price change over available period | last adj_close / first adj_close − 1 | Per ticker, selected year |
| Last available close | Last observed prices.close | Per ticker, selected year |
| Intraday range | (high−low)/close | Single company/day |
| Unusual range flag | daily_range_pct >= per-ticker full-sample 95th percentile | Compute in cleaning before year filtering |
| Flag count | Sum is_flagged | Selected ticker/year |
| Largest range | Maximum daily_range_pct | Selected ticker/year |
| Trading days | Count observed price rows | Selected ticker/year |
| Co-flags | Sum is_flagged across eight stocks on date | Full eight-stock universe; unaffected by stock/legend selection |
| News window | Same symbol; D−7 <= date <= D | Calendar dates, not only year/trading days |
| Filing context | Latest filing date <= D | Same symbol; includes previous years |

Use adjusted prices consistently at both endpoints of period comparisons.
Unadjusted last close is a separate historical dollar quote. Do not call the
indexed change total shareholder return or annualize partial-year changes.
Intraday range is neither a close-to-close return nor evidence of direction.
Full-sample thresholds are retrospective; do not market them as real-time signals.

## 8. Analysis architecture and contracts
Code is separate from this specification; no analysis implementation belongs here.

| Module | Responsibility | Outputs |
|---|---|---|
| cleaning.py | Agreed cleaning, fixed flags, joins | Four canonical Parquet files, cleaning log, samples |
| data_loader.py | Load schemas, validate complete data and links | Dictionary of validated DataFrames |
| analysis.py | Pure filtering/aggregation/context lookup | Values/DataFrames described below |
| phase2.py | Validate full data and export all planned backend outputs | CSVs and JSON report in outputs/analysis |
| charts.py (Phase 3) | Build Plotly figures from analysis outputs | Figures |
| app.py (Phase 3) | Controls, state, formatting and layout | Interface |

`year_coverage(prices, year)` returns dates/company count/coverage label.
`year_summary(prices, context, year)` returns eight summary rows.
`indexed_prices(prices, year)` returns symbol/date/adj_close/indexed_price/period_change.
`stock_series(context, year, symbol)` returns date-sorted context rows.
`flagged_days(context, year, symbol)` returns ranked flagged rows.
`initial_date(context, year, symbol)` returns Timestamp or None.
`date_comparison(context, date)` returns eight tickers, range, flags and co-flag count.
`news_context(news, symbol, date)` returns descending-date eligible news rows.
`filing_context(filings, symbol, date)` returns filing dictionary or None, optional
annual risk fallback dictionary or None, and same-day flag.

Functions receive frames with validated schemas/datetime columns and return new
objects without mutating inputs. They do not access UI session state, network,
or globals containing mutable data. Unsupported years/tickers fail clearly.

## 9. Technical choices and performance
Python/pandas for analysis; pyarrow/Parquet for compact typed storage; Streamlit
and Plotly for Phase 3. Tables are small enough for memory; no database or AI API
is required. The provided Phase 2 requirements file is an independent reproducible
analysis environment; the original branch's uv metadata is archived under docs/original_environment/ as provenance.

Load once through a future Streamlit cache keyed by cleaned-file paths, sizes,
and modification timestamps. Validate on each newly loaded version. Filtering
happens in memory. Keep long news/filing text in separate tables and retrieve by
keys/as-of lookup. Do not duplicate it into every price row. Do not fetch live
sources during UI interactions. Dependency additions should not alter metric rules.

Missing data files: identify paths and point to README preparation commands;
stop dependent processing. No silent sample substitution. Raw source stays local;
include agreed cleaned files on main as required for Phase 2.

## 10. Data cleaning baseline and limitations
Retain the supplied rules: standardize tickers/dates, validate types and OHLC,
clean HTML entities and outer filing whitespace, preserve original observations,
keep weekend news and pre-price-window filings, flag short news (<300 characters),
flag short risk text (<2,000 characters), derive normalized range, and build same-day
news and backward filing links. No imputation or outlier removal.

Short-text flags are heuristics, not verified semantic classifications. Apply
annual fallback only to referring 10-Qs; keep original text visible. The source
has LLM news summaries, no publication times, no market index, and only eight
large companies over a short period. The supplied log is evidence for one branch;
it cannot establish team reconciliation. Validate complete raw inputs before
cleaning; canonical loader validates complete derived data afterwards.

## 11. Build order and acceptance
1. Obtain pinned source and compare supplied team cleaning work; record agreements.
2. Run cleaning and validate full canonical files; commit cleaned files on main.
3. Run backend exports and tests; inspect generated year summaries/context examples.
4. In Phase 3, build overview, stock/date controls, then context panels.
5. Give a fresh coding agent the repository and this spec; record questions/guesses,
   fix material gaps, and repeat relevant checks. This package contains a prompt,
   not a claim that the fresh-agent test already happened.

Acceptance:
- Default 2025; three tabs; eight overview stocks; correct partial-year labels.
- Every indexed series starts at 100; period change matches adjusted endpoints.
- Year filters affect price views/counts, not original thresholds or context windows.
- Flagged table and initial/tie selections match backend outputs.
- Co-flag count always uses eight stocks; legend changes never change metrics.
- Correct news window, no future filing, same-day label, valid annual fallback.
- Empty/missing content has explicit messages; unknown values never become zero.
- Backend runs without UI, returns reusable values, and preserves input frames.
- Full canonical validation and example exports pass before marking data ready.

## 12. Do and don't rules
**Do:** use full canonical data, check IDs/dates/types/uniqueness, show actual
coverage, keep ticker colors/units consistent, use text labels as well as color,
format dates YYYY-MM-DD, dollars/percentages to two decimals and counts as integers,
collapse long text, retain eight-stock overviews, and document unavailable evidence.

**Don't:** fabricate rows or results; treat samples/fixtures as team data; impute
weekend prices; remove extremes; recalculate thresholds by year; mix adjusted and
unadjusted comparison endpoints; use future context; call historical quotes live;
claim causality or market-wide proof; add predictions/trading advice; generate
unsupported summaries; expose credentials; couple analysis to UI state; or state
that unperformed team/fresh-agent/full-source checks passed.
