# Progress Log

Claude Code: read this at the start of every session and update it at the end of every phase or major step.

## Current status
- Phase 1 (vision write-up + usage example): done. Intended user: investor-relations analyst.
- Phase 2 cleaning deliverable: done. The team adopted Shreya's cleaning (`data/cleaned/`, from branch `cleaning-shreya`) as the canonical dataset. Merged and pushed to main on GitHub (commit 2be2e40).
- Remaining Phase 2 work: BUILD_SPEC.md and the backend analysis code (brief in `phases/phase-2.pdf`).

## What exists so far
- In the repo: cleaned data (4 parquet files in `data/cleaned/`), cleaning script (`src/dso576_python/cleaning.py`), decision log (`docs/cleaning_decision_log.md`), change log (`outputs/cleaning_changes.csv`), and sample files (`sample/`).

## Phase 3 note: Grant's dashboard prototype
Grant pushed a Streamlit prototype to main as `SHARE_DASHBOARD.zip` / `.tar.gz` (commits 65daf90, 166770b; both archives hold the same 9 files). It is Phase 3 material and is not extracted onto main. Issues found in a read-only review (2026-10-18), to fix before using it:
- `app.py` imports `dso576_python.charts`, but `charts.py` sits at the archive root, so the app won't start as packaged.
- `data_loader.py` imports `cleaning.py`, which the archive leaves out, so validation crashes on startup (`ModuleNotFoundError`, not caught by the app).
- MD&A and risk text are shown in full; the agreed MVP shows the first ~2,000 characters with an expander for the rest.
- The "refers to 10-K" quality label (`risk_refers_to_10k`) is never shown.
- `$` signs: `st.markdown` treats text between two `$` as LaTeX math; all 73 MD&A texts and 824 news summaries contain 2+ `$` amounts, so text will likely garble (not run-tested).
- `streamlit>=1.35` may be too low for `st.segmented_control` (unverified); its `requirements.txt` also pins pandas 2.2.3, conflicting with our pandas 3.0.6 environment.
- Code is dense (long one-liners), not beginner-level per CLAUDE.md Section 5.

## Decisions made
- Context, not causation: the tool never claims a news item or filing caused a price move.
- Output is a shortlist for human follow-up.
- Python only; beginner-level code for team readability; no paid APIs.

## Open questions
- Whether the course requires anything specific about the "live tool" format (check the phase brief).

## Phase history
| Phase | Brief | Status | Notes |
|-------|-------|--------|-------|
| 1 | vision + usage example | Done | |
| 2 | `phases/phase-2.pdf` | In progress | Cleaning deliverable done (Shreya's cleaning adopted as canonical). Remaining: BUILD_SPEC.md, backend analysis code. |
