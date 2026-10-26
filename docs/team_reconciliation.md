# Team Cleaning Reconciliation

## Decision
The team adopted Shreya's cleaning (branch `cleaning-shreya`, merged to `main` in `2be2e40`) as the one canonical analysis-ready dataset in `data/cleaned/`. The teammates deferred to her judgement on the cleaning choices. **This comparison was written afterwards (2026-10-18)** to document where the individual Module 6 versions agree and differ. It records each branch's actual code and notebook output; it does not state teammates' reasons beyond what their own files say.

## Branches compared (read-only, from GitHub)
| Branch | Tip | Files used as evidence | Comparable? |
|--------|-----|------------------------|-------------|
| `branch_Sumin` | `9f41254` | `cleaning_Sumin.py`, `cleaning_Sumin.ipynb` (with outputs), `prices_cleaned_sample.csv` | Yes |
| `branch_Victor` | `b235c3f` | `data_cleaning.py`, `data_cleaning_victor.ipynb` (with outputs), `cleaned_sample.csv` | Yes |
| `branch_grant` | `9bf78a2` | `cleaning_scripts.py`, `grant-README.md`, `data_sample.csv` | Yes (generated `outputs/` files are not committed, so only code, README and sample were compared) |
| `branch_haley` | `b4569f3` | `README.md`, `scripts/clean_spotify_financials.py` | **No.** It cleans Spotify Technology S.A. annual financial facts (SEC company facts), from the team's earlier project idea, not the Herculean tables. |

**Same source data:** Sumin's, Victor's and Grant's work all report 2,656 price, 3,888 news and 73 filing rows. Sumin's and Victor's notebooks also report total volume 159,456,800,900, matching the canonical data. None of the three recorded a pinned dataset revision (Victor records a download date, 2026-10-02); the canonical version pins revision `52d3ecb` and SHA-256 hashes.

## Comparison
| Topic | Sumin | Victor | Grant | Canonical choice (`main`) | Agreement |
|-------|-------|--------|-------|---------------------------|-----------|
| **Unit of analysis / keys** | prices and news: symbol + date; filings: checked symbol + date (0 repeats) | Same row definitions; 0 repeated symbol–date | Keys: prices and news symbol + date; filings symbol + date + document_type; 0 repeated symbol–date filings | Same keys; plus `price_context`: one row per trading day | ✅ Agree |
| **Duplicates** | 0 exact, 0 repeated IDs, 0 repeated keys; keep all rows | Same counts; keep all rows | Same counts; reports rather than removes | Same counts; no deduplication (R7) | ✅ Agree |
| **Missing values** | 0 nulls; keep all rows | 0 before and after | 0; would keep and report, never fill | 0 before and after; no imputation (R9) | ✅ Agree |
| **Types** | `date` object → datetime | `date` object → datetime (`errors="coerce"`, asserts 0 failures) | `date` object → datetime; failures would be kept as NaT and reported | `date` object → datetime64; any failure stops the script (R1) | ✅ Agree on conversion. Differ only on what would happen to a failed date; none occurred |
| **Labels and text** | No text checks in the notebook | Checked symbols and document types for whitespace and consistency; kept all text unchanged, **including HTML entities** (e.g. `&#8217;`) | Checked whitespace and lengths of all text columns; kept text exactly, **including leading/trailing whitespace**; trimming left "for review" | Filing MD&A and risk text: decode HTML entities and strip outer whitespace only (R4, 73 + 73 rows). News text unchanged; adds `highlights_low_info` and `risk_refers_to_10k` flags (R5, R6) | ⚠️ **Differ.** Victor and Grant kept filing text exactly as downloaded; the canonical version decodes entities and trims outer whitespace |
| **Joins** | None | prices → news, left join on symbol + date, `validate="one_to_one"`; 2,656 → 2,656, 0 unmatched (in memory, not saved) | Latest filing on or before each price date (same day allowed; tie order by date, document type, id); news counts for D−7 through D | prices → news one-to-one; latest filing and latest 10-K as-of (same day allowed, `filed_same_day` flag); saved in `price_context` (R13) | ✅ Agree where implemented. Grant's tie order never applies (0 same-date filings) |
| **Exclusions** | None | None | None; weekend and holiday news explicitly kept | None; weekend news and pre-window filings kept (R10, R11) | ✅ Agree |
| **Derived fields** | None | `daily_range = high − low` in dollars; sample = 50 largest dollar ranges (26 META, 20 TSLA rows). His limitations note says dollar ranges are not normalized across companies | Both `high − low` and `(high − low) / close`; **no threshold applied** (left pending a team decision) | `daily_range_pct = (high − low) / close`; flag = at or above each company's 95th percentile (fixed MVP rule); `co_flag_count` (R8, R12) | ⚠️ **Differ.** Victor used the dollar range; Grant computed both and chose no threshold; the canonical version uses the normalized range with a fixed per-company 95th percentile |
| **Outputs** | 50-row prices sample only | 50-row prices sample; cleaned tables kept in memory | Script writes cleaned Parquet and lookups to `outputs/` (not committed); 48-row sample across all three tables | Four cleaned Parquet files committed in `data/cleaned/`, change log, 50-row sample | Canonical is the only version with committed full cleaned files |
| **Environment** | pandas 2.2.2, pyarrow 14.0.2 | pandas 3.0.5, pyarrow 25.0.1 | pandas 2.3.3, pyarrow 25.0.1 | pandas 3.0.6, pyarrow 25.0.1 (`uv.lock`) | Differ; canonical uses `uv.lock` |

## Resolution
| Disagreement | Adopted resolution | Effect on the data |
|--------------|--------------------|--------------------|
| Filing text kept exactly vs. entities decoded and trimmed | Canonical: decode HTML entities and strip outer whitespace; no other text edits | Changes display only; wording is identical (verified: cleaned = `unescape(raw).strip()` for every row) |
| Dollar range vs. normalized range; threshold undecided | Canonical: normalized range, fixed per-company 95th percentile | Determines which 136 days are flagged (17 per company) |
| Failed-date policy (keep as NaT vs. stop) | Canonical: stop with an error | None in practice: 0 failures in every version |

All other topics already agreed. Haley's branch is out of scope for this dataset.
