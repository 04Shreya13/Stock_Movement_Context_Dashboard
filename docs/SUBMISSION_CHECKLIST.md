# Phase 2 Submission Checklist: Open Items

Already done (see `docs/validation_report.md`): canonical cleaned data on `main`, backend code and tests, full-data validation.

- [x] **Team reconciliation.** Comparison of Sumin's, Victor's and Grant's Module 6 cleaning against the adopted canonical version, with the disagreements and how each was resolved (`docs/team_reconciliation.md`). Haley's branch is Spotify data and not comparable.
- [x] **Spec fixes in `BUILD_SPEC.md`.**
  - [x] Full-range period selector as the default (year options available).
  - [x] Flag threshold stated plainly as a fixed MVP choice: per-company 95th percentile.
  - [x] Gaps closed: Python and UI dependencies, filing text shown as the first ~2,000 characters with an expander, no chart-point selection, quality labels defined, local Streamlit deployment plus one sentence on later deployment, `outputs/analysis/` git-ignored.
  - [x] Each backend function's returned keys and columns listed (checked against the real outputs).
  - [x] Shared constants for tickers and periods (`constants.py`); `data_loader` no longer imports `analysis`.
  - [x] Status notes and repeated warnings removed.
- [ ] **Fresh-agent test.** Give a fresh coding agent the repo and `BUILD_SPEC.md`, record every question or guess, fix the gaps, and record the findings.
