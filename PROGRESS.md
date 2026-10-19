# Progress Log

Claude Code: read this at the start of every session and update it at the end of every phase or major step.

## Current status
- Phase 1 (vision write-up + usage example): done. Intended user: investor-relations analyst.
- Phase 2 cleaning deliverable: done. The team adopted Shreya's cleaning (`data/cleaned/`, from branch `cleaning-shreya`) as the canonical dataset. Merged to main; push to the remote is pending.
- Remaining Phase 2 work: BUILD_SPEC.md and the backend analysis code (brief in `phases/phase-2.pdf`).

## What exists so far
- In the repo: cleaned data (4 parquet files in `data/cleaned/`), cleaning script (`src/dso576_python/cleaning.py`), decision log (`docs/cleaning_decision_log.md`), change log (`outputs/cleaning_changes.csv`), and sample files (`sample/`).

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
