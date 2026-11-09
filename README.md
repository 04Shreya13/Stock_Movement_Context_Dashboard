# Stock Movement Context Dashboard

DSO 576, USC Marshall. When one of eight large stocks has an unusually wide trading day, this dashboard shows what else was happening around it, so an analyst knows where to look first.

| | |
|---|---|
| **Live app** (no sign-in needed) | https://04shreya13.github.io/Stock_Movement_Context_Dashboard/ |
| **Demo video** | _Link to be added_ |
| **Repository** | https://github.com/04Shreya13/Stock_Movement_Context_Dashboard |

> This tool shows context, not causation. It does not explain why a stock moved, predict prices, or give investment advice.

## Intended user and decision
An **investor-relations analyst** at a large investment firm has to explain unusual stock moves before speaking with investors.

| The analyst selects | The dashboard shows | The analyst decides |
|---|---|---|
| A period | Eight stocks compared, with a summary table | Which stock to investigate |
| A stock | Its price chart and unusually wide days, ranked | Which day to review |
| A flagged day | How all eight stocks moved that day, nearby news, the latest filing | Whether the move looks company-specific or shared, and what to read |
| A news item or filing | Selected sentences and the full text | Which evidence to verify |
| The shortlist button | Saved days, exportable as CSV | Which days go forward for human follow-up |

**Key measure:** daily range = (high − low) ÷ close, as a percentage of the closing price. A day is flagged when its range is in that company's top 5%.

## Video Demonstration
Product Video Demonstration Link:
https://drive.google.com/file/d/1LE_wqrYsOmughFZQcsRuLhHJUFQ3D0jD/view?usp=sharing

## Run it locally
You only need Python 3. From the project root:

```bash
python3 app.py
```

The site opens at http://127.0.0.1:8501. Press Ctrl+C to stop.

For development, with [uv](https://docs.astral.sh/uv/) installed:

```bash
uv sync
PYTHONPATH=src uv run python -m unittest discover -s tests -v    # run the tests
PYTHONPATH=src uv run python -m dso576_python.export_web         # rebuild web/data.js after a data or backend change
```

## Data scope
- **Source:** [Herculean](https://huggingface.co/datasets/TheFinAI/Herculean) (TheFinAI, CC BY 4.0), pinned to revision `52d3ecb`.
- **Companies:** Apple, Adobe, Amazon, Alphabet, Meta, Microsoft, Nvidia, Tesla.
- **Period:** prices from 2024-12-02 to 2026-03-31 (2024 is December only; 2026 is January to March).
- **Records:** 2,656 daily prices, 3,888 daily news summaries, 73 filings (10-K and 10-Q).
- **No subset or sample is used in the app.** It shows the full cleaned tables, and 136 days are flagged, 17 per company.

## Current limitations
- **It cannot establish causes.** News and filings are shown because they are close in time, not because they explain a move.
- **There is no market index.** The count of stocks flagged on the same day is only a partial check for market-wide moves.
- **Flags look back.** Each cutoff uses a company's full history, including later days, so flags are not a real-time signal.
- **A wide range is not a large return.** The daily range measures the swing within a day and misses overnight gaps.
- **News items are AI-written summaries**, with no publication times or article links, and may contain errors.
- **Filings are excerpts** of the MD&A and risk sections and can be weeks or months old; the app shows their age.
- **Selected sentences are picked by keywords.** They are not ranked by importance and are not a summary.
- **Some 10-Q risk sections only update the 10-K.** Those not labelled "refers to 10-K" can look like a complete risk list.
- **The shortlist is saved only in your browser.** Export it to keep a copy.
- **Scope is narrow:** eight very large companies over about 16 months.

## How the project is organized
```
web/                     The dashboard site, published automatically by GitHub Pages
app.py                   Serves web/ on your own computer
src/dso576_python/       Python backend: cleaning, validation, analysis, data export
data/cleaned/            The team's agreed dataset
tests/                   Automated tests
BUILD_SPEC.md            What the dashboard must do
PROGRESS.md              What is done and what is left
AGENTS.md                Standing instructions for coding agents
docs/                    Decision logs, validation report, data reference, Phase 1 proposal
data_cleaning.ipynb      Evidence notebook for the cleaning
sample/, outputs/        Cleaned sample and the cleaning change log
```

Full data dictionary and pipeline details: [`docs/data_and_pipeline.md`](docs/data_and_pipeline.md).

## Team
Grant Wu, Haley Wong, Shreya, Sumin Kang, Victor Teng Wang

<sub>For educational purposes only. Not investment advice.</sub>
