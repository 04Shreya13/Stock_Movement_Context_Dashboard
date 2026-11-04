# Change requests

## Claims

| Auditor | Feature audited | Number audited | Version checked |
|---|---|---|---|
| Haley Wong | Selecting a flagged trading day and viewing its event context | AAPL normalized daily range on 2025-04-09 | `8ace87fa46a1ab58d7d9ed216f49e7513c29f33b` |

## CR-HW-001 — Make the shared dashboard package runnable

- **Status:** Open
- **Requested by:** Haley Wong
- **Area:** `SHARE_DASHBOARD.zip` packaging and startup
- **Evidence:** `SHARE_DASHBOARD/app.py` imports
  `dso576_python.charts`, but the archive stores `charts.py` at
  `SHARE_DASHBOARD/charts.py`, not inside the package. In addition,
  `dso576_python/data_loader.py` imports `dso576_python.cleaning`, but the
  archive does not contain `dso576_python/cleaning.py`. These missing module
  paths prevent the app from starting, so an investor-relations analyst cannot
  reach the flagged-day workflow.
- **Reproduce:** From the repository root, run
  `uv run --frozen python scripts/audit_haley.py`. The feature check reports the
  archive entries that are present and missing.
- **Requested change:** Put `charts.py` and `cleaning.py` inside the packaged
  `dso576_python` directory (or update imports and remove the unavailable
  dependency), extract the app into the repository's normal source layout, and
  add a clean-environment startup test that reaches the flagged-day table.
- **Acceptance check:** From a fresh clone, following the documented Windows or
  macOS/Linux commands starts the dashboard without an import error. Selecting
  AAPL and a flagged date updates the event metrics, eight-stock comparison,
  news, and filing panels.

## Number audit outcome — no change requested

The stored AAPL daily-range percentage for 2025-04-09 matches an independent
calculation from `high`, `low`, and `close`, and all 332 AAPL rows match the
documented formula within `1e-12`. The metric check did not find a calculation
bug. UI display remains unobserved until CR-HW-001 is resolved.
