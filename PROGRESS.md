# Progress Log

Coding agents: read this at the start of every session and update it at the end of every phase or major step.

## Current status (2026-11-09)
- **Phase 1:** vision and data-fit PDF done (`docs/phase1_proposal.pdf`).
- **Phase 2:** cleaning, `BUILD_SPEC.md` and backend done. The fresh-agent test was never run or recorded (`docs/SUBMISSION_CHECKLIST.md`).
- **Phase 3 (MVP, due 2026-11-09):** one merged dashboard is on `main` in `web/`.
  - It combines Haley's site (layout, shortlist, CSV export, selected sentences) with the Streamlit version's analysis views (eight-stock chart, summary table, same-day comparison, fixed flags).
  - The browser only displays values from `web/data.js`, written by `export_web.py` through the tested backend.
  - Tests: 18 pass.

## Still to do for Phase 3
- [ ] Publish to GitHub Pages and check the live link in an incognito window.
- [ ] Record the 3-6 minute demo video and add its link to `README.md`.
- [ ] Choose the showcase preference (all members agree / do not share publicly / decide later).
- [ ] Submit the app, video and repository links on Gradescope (one submission per team).

## Open items after the MVP
- Audit CR-SHREYA-01: 10-Q risk sections that only update the 10-K can look complete. CR-02 (filing age) and CR-03 (look-ahead caption) are done.
- `change-requests.md` is on the local branch `audit-shreya` only and has not been pushed.
- Sumin's Module 10 tests are on `module10_sumin`. They need `pytest`, which is not a project dependency.

## Where older work lives
- Standalone Streamlit version: branch `audit-app-shreya` (the commit audited in Module 9).
- Individual Module 6 cleaning: branches `cleaning-shreya`, `branch_Sumin`, `branch_Victor`, `branch_grant`.
- Grant's first prototype archives were removed from `main` and remain in git history (commits 65daf90, 166770b).

## Decisions made
- Context, not causation: the tool never claims a news item or filing caused a price move.
- Output is a shortlist for human follow-up.
- Python for all data and analysis, with a static HTML front end. No paid APIs.
- Flags are fixed at each company's 95th percentile and never recomputed.
- Hosting is GitHub Pages, so the instructor can open the app with no sign-in. Free Pages needs a public repository.

## Phase history
| Phase | Brief | Status | Notes |
|-------|-------|--------|-------|
| 1 | vision + data fit | Done | |
| 2 | `phases/phase-2.pdf` | Built | Fresh-agent test not done |
| 3 | MVP, due 2026-11-09 | In progress | Dashboard merged; deployment, video and submission remain |
