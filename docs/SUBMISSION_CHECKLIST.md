# Phase 2 Submission Checklist: Open Items

Already done (see `docs/validation_report.md`): canonical cleaned data on `main`, backend code and tests, full-data validation.

- [ ] **Team reconciliation.** Write up the comparison of Sumin's, Victor's and Grant's Module 6 cleaning against the adopted canonical version: disagreements found and how each was resolved (`docs/team_reconciliation.md`).
- [ ] **Spec fixes in `BUILD_SPEC.md`.**
  - [ ] Full-range period selector as the default (year options available).
  - [ ] State the flag threshold plainly as a fixed MVP choice: per-company 95th percentile.
  - [ ] Close the open gaps: Python and UI dependency versions, filing text shown as the first ~2,000 characters with an expander, no chart-point selection, quality labels defined, local Streamlit deployment plus one sentence on later deployment, where `outputs/analysis/` lives.
  - [ ] List each backend function's returned keys and columns.
  - [ ] Shared constants for tickers and years (decouple `data_loader` from `analysis`).
  - [ ] Remove status notes and repeated warnings.
- [ ] **Fresh-agent test.** Give a fresh coding agent the repo and `BUILD_SPEC.md`, record every question or guess, fix the gaps, and record the findings.
