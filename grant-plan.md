# Data Cleaning Check and Validation List

Use this checklist to review the inspection results and proposed next steps for each table. **Checked** means the check was run on the supplied Parquet data; **To do** means evidence or a decision is still needed. No additional cleaning is applied by this document.

## Shared project checks

| Assignment item | Check and why | Result | Verify |
|---|---|---|---|
| **1. Project question** | Confirm the business question, purpose, and main measure. | **Checked:** The project is to flag unusually wide price movements and show news and filing context for analyst review. The flagging choice remains open: the project description refers to both raw and normalized range. | [ ] |
| **3. Preserve source** | Record source/version and keep originals unchanged. | **Checked:** Source is TheFinAI/Herculean on Hugging Face; the supplied data are Parquet files. The source version or download date is not recorded in the provided documents. Original data files were not changed during inspection. | [ ] |
| **13. Reproducibility** | Restart and run all code from original inputs to verify submitted outputs. | **To do:** A fresh full run from the original inputs has not been verified. | [ ] |
| **14. Limitations** | Record issues that could affect interpretation. | **Checked:** The project description says the data cannot establish causation and may omit broader market, macroeconomic, and industry factors. | [ ] |

## Prices (`prices.parquet`)

| Assignment item | Check and why | Result | Verify |
|---|---|---|---|
| **2. Define one row** | Check the row meaning and candidate key. | **Checked:** One company per trading day; `(symbol, date)` has 0 duplicates. | [ ] |
| **4. Types** | Inspect types and count failed date conversions. | **Checked:** `date` loaded as text and parsed to datetime with 0 failures. `id` is integer; price and volume fields are numeric. Results are shown in the notebook. | [ ] |
| **5. Standardize text** | Check symbol consistency while preserving meaningful text and IDs. | **Checked:** Symbols are uppercase with no surrounding whitespace; no symbol cleanup appears necessary. | [ ] |
| **6. Duplicates** | Count exact duplicates, repeated IDs, and repeated natural keys separately. | **Checked:** 0 exact duplicate rows, duplicate IDs, or duplicate `(symbol, date)` keys. | [ ] |
| **7. Missing data** | Count nulls before deciding whether to fill or drop. | **Checked:** 0 nulls in all 9 columns. | [ ] |
| **8. Suspicious values** | Check impossible or implausible price and volume values. | **Checked:** 0 nonpositive prices, `high < low` violations, open/close outside daily low-high bounds, or negative volumes. | [ ] |
| **9. Verify merges** | Check date-key coverage with news and avoid unintended row loss. | **Checked:** All 2,656 price `(symbol, date)` keys have same-day news. **To do:** The seven-day news window and filing lookup have not yet been validated. | [ ] |
| **10. Reconcile changes** | Compare starting and final row counts and explain differences. | **Checked:** Starting count is 2,656. **To do:** A final cleaned count is unavailable because the remaining cleaning workflow has not been applied. | [ ] |
| **11. Check calculations** | State metric definitions, denominators, and missing-group handling. | **To do:** Movement metrics and their denominators have not yet been calculated or documented. | [ ] |
| **12. Verify records** | Compare expected and actual output for five representative records. | **To do:** Five expected-versus-actual record checks have not yet been completed. | [ ] |

## News (`news.parquet`)

| Assignment item | Check and why | Result | Verify |
|---|---|---|---|
| **2. Define one row** | Check the row meaning and candidate key. | **Checked:** One company per calendar day; `(symbol, date)` has 0 duplicates. | [ ] |
| **4. Types** | Inspect types and count failed date conversions. | **Checked:** `date` loaded as text and parsed to datetime with 0 failures. `id` is integer; other fields are object/text. | [ ] |
| **5. Standardize text** | Check symbol consistency and empty or padded summaries. | **Checked:** Symbols are uppercase with no surrounding whitespace. Highlights are nonempty and have no surrounding whitespace. | [ ] |
| **6. Duplicates** | Count exact duplicates, repeated IDs, and repeated natural keys separately. | **Checked:** 0 exact duplicate rows, duplicate IDs, or duplicate `(symbol, date)` keys. | [ ] |
| **7. Missing data** | Count nulls before deciding whether to fill or drop. | **Checked:** 0 nulls in all 4 columns. | [ ] |
| **8. Suspicious values** | Check invalid dates and investigate dates that could be mistaken for bad records. | **Checked:** All dates parse. Weekend and holiday dates are expected because news is recorded by calendar day. | [ ] |
| **9. Verify merges** | Check same-day coverage and preserve news useful to a date-window lookup. | **Checked:** 2,656 of 3,888 news rows match same-day prices; 1,232 do not. Keep unmatched calendar-day records for the prior-seven-day context. **To do:** Validate the actual date-window retrieval. | [ ] |
| **10. Reconcile changes** | Compare starting and final row counts and explain differences. | **Checked:** Starting count is 3,888. **To do:** A final cleaned count is unavailable because the remaining cleaning workflow has not been applied. | [ ] |
| **11. Check calculations** | Report context-window counts and how missing group keys are handled. | **To do:** News-window counts and denominator handling have not yet been calculated or documented. | [ ] |
| **12. Verify records** | Compare expected and actual output for five representative records. | **To do:** Five expected-versus-actual record checks have not yet been completed. | [ ] |

## Filings (`filings.parquet`)

| Assignment item | Check and why | Result | Verify |
|---|---|---|---|
| **2. Define one row** | Check the row meaning and candidate key. | **Checked:** One 10-K or 10-Q per company; `(symbol, date, document_type)` has 0 duplicates. There are no repeated `(symbol, date)` pairs. | [ ] |
| **4. Types** | Inspect types and count failed date conversions. | **Checked:** `date` loaded as text and parsed to datetime with 0 failures. `id` is integer; text fields are object/string. | [ ] |
| **5. Standardize text** | Check labels and content without changing meaningful filing text. | **Checked:** Symbols and document types are consistently uppercase; no content is empty. All 73 MD&A and risk text values have surrounding whitespace. **Proposed for review:** consider trimming only leading/trailing whitespace while preserving internal text. | [ ] |
| **6. Duplicates** | Count exact duplicates, repeated IDs, and repeated filing keys separately. | **Checked:** 0 exact duplicate rows, duplicate IDs, or candidate filing-key duplicates. | [ ] |
| **7. Missing data** | Count nulls before deciding whether to fill or drop. | **Checked:** 0 nulls in all 6 columns. | [ ] |
| **8. Suspicious values** | Check invalid dates and unusually short or long content without assuming it is wrong. | **Checked:** All dates parse. Risk text lengths range from 333 to 196,794 characters. Unusual length alone is not evidence of an error; review examples rather than dropping them. | [ ] |
| **9. Verify merges** | Confirm the selected filing is available at the event date and does not come from the future. | **To do:** Latest-filing-on-or-before-event-date selection has not yet been tested. | [ ] |
| **10. Reconcile changes** | Compare starting and final row counts and explain differences. | **Checked:** Starting count is 73. **To do:** A final cleaned count is unavailable because the remaining cleaning workflow has not been applied. | [ ] |
| **11. Check calculations** | Document how filing selection and missing group keys affect event-level results. | **To do:** Filing selection checks and missing-group handling have not yet been evaluated. | [ ] |
| **12. Verify records** | Compare expected and actual output for five representative records. | **To do:** Five expected-versus-actual record checks have not yet been completed. | [ ] |

## Additional data checks

These checks supplement the assignment because they help identify gaps or inconsistencies across the three source tables.

| Check and why | Result | Verify |
|---|---|---|
| Compare row coverage by symbol to spot unexpected gaps or imbalances. | **Checked:** Each of the eight symbols has 332 price rows and 486 news rows. Filings have 9 records per symbol, except ADBE, which has 10. | [ ] |
| Compare daily news dates with price dates so non-trading dates are not mistaken for missing prices. | **Checked:** 2,656 news symbol/date records match prices; 1,232 do not. The project uses calendar-day news and trading-day prices, so retain those unmatched news records for date-window context. | [ ] |
