"""Clean Spotify annual financial facts from the SEC Company Facts JSON.

The raw JSON is never modified. This script uses only Python's standard library.
Run from the project root with:
    python scripts/clean_spotify_financials.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "spotify_companyfacts_2026-10-03.json"

# The friendly names are deliberately fixed rather than inferred so downstream users
# do not have to understand XBRL concept naming conventions.
METRICS = {
    "Revenue": "revenue",
    "GrossProfit": "gross_profit",
    "ProfitLossFromOperatingActivities": "operating_profit_loss",
    "ProfitLoss": "net_profit_loss",
    "CashFlowsFromUsedInOperatingActivities": "operating_cash_flow",
    "CashAndCashEquivalents": "cash_and_cash_equivalents",
}

OUTPUT_FIELDS = [
    "record_id",
    "calendar_year",
    "metric",
    "value_eur",
    "unit",
    "period_start",
    "period_end",
    "fact_type",
    "form",
    "filed_date",
    "accession_number",
    "source_fiscal_year",
    "source_fiscal_period",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_iso(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {field}: {value!r}") from exc


def flatten_selected_facts(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Return all filing contexts for the selected Spotify financial concepts."""
    facts = document.get("facts", {}).get("ifrs-full", {})
    rows: list[dict[str, Any]] = []
    for concept, metric in METRICS.items():
        if concept not in facts:
            raise KeyError(f"Required IFRS concept is missing: {concept}")
        for unit, observations in facts[concept].get("units", {}).items():
            for item in observations:
                row = {
                    "taxonomy": "ifrs-full",
                    "concept": concept,
                    "metric": metric,
                    "unit": unit.strip().upper(),
                    "period_start": item.get("start", ""),
                    "period_end": item.get("end", ""),
                    "value": item.get("val"),
                    "accession_number": str(item.get("accn", "")).strip(),
                    "source_fiscal_year": item.get("fy", ""),
                    "source_fiscal_period": str(item.get("fp", "")).strip().upper(),
                    "form": str(item.get("form", "")).strip().upper(),
                    "filed_date": item.get("filed", ""),
                    "frame": item.get("frame", ""),
                }
                rows.append(row)
    return rows


def is_calendar_annual(row: dict[str, Any]) -> tuple[bool, str]:
    """Identify comparable annual 20-F facts and explain excluded records."""
    if row["form"] != "20-F" or row["source_fiscal_period"] != "FY":
        return False, "not_annual_20f"
    if row["unit"] != "EUR":
        return False, "not_eur"
    end = parse_iso(row["period_end"], "period_end")
    if end.month != 12 or end.day != 31:
        return False, "not_calendar_year_end"
    if row["period_start"]:
        start = parse_iso(row["period_start"], "period_start")
        duration = (end - start).days + 1
        if duration not in (365, 366):
            return False, "not_full_calendar_year"
    if not isinstance(row["value"], (int, float)) or isinstance(row["value"], bool):
        return False, "non_numeric_value"
    parse_iso(row["filed_date"], "filed_date")
    return True, "eligible"


def clean(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    """Filter annual facts and choose the newest filing for each metric/year/unit."""
    eligible: list[dict[str, Any]] = []
    exclusions: Counter[str] = Counter()
    conversion_failures: list[str] = []
    for row in rows:
        try:
            keep, reason = is_calendar_annual(row)
        except ValueError as exc:
            keep, reason = False, "invalid_date"
            conversion_failures.append(str(exc))
        if keep:
            eligible.append(row)
        else:
            exclusions[reason] += 1

    groups: dict[tuple[str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in eligible:
        year = parse_iso(row["period_end"], "period_end").year
        groups[(row["metric"], year, row["unit"])].append(row)

    cleaned: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    value_conflict_groups = 0
    for (metric, year, unit), candidates in sorted(groups.items(), key=lambda x: (x[0][1], x[0][0])):
        ordered = sorted(candidates, key=lambda r: (r["filed_date"], r["accession_number"]))
        winner = ordered[-1]
        unique_values = {row["value"] for row in candidates}
        if len(unique_values) > 1:
            value_conflict_groups += 1
        record_id = f"{year}-{metric}-{unit.lower()}"
        cleaned.append(
            {
                "record_id": record_id,
                "calendar_year": year,
                "metric": metric,
                "value_eur": winner["value"],
                "unit": unit,
                "period_start": winner["period_start"],
                "period_end": winner["period_end"],
                "fact_type": "duration" if winner["period_start"] else "instant",
                "form": winner["form"],
                "filed_date": winner["filed_date"],
                "accession_number": winner["accession_number"],
                "source_fiscal_year": winner["source_fiscal_year"],
                "source_fiscal_period": winner["source_fiscal_period"],
            }
        )
        for candidate in ordered:
            audit.append(
                {
                    "record_id": record_id,
                    "metric": metric,
                    "calendar_year": year,
                    "value_eur": candidate["value"],
                    "filed_date": candidate["filed_date"],
                    "accession_number": candidate["accession_number"],
                    "kept": candidate is winner,
                    "decision": "latest_filing_kept" if candidate is winner else "older_filing_context_removed",
                }
            )

    ids = [row["record_id"] for row in cleaned]
    exact_duplicate_rows = len(rows) - len({json.dumps(r, sort_keys=True) for r in rows})
    repeated_business_keys = sum(len(v) - 1 for v in groups.values())
    audit_summary = {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "selected_source_rows": len(rows),
        "exact_duplicate_source_rows": exact_duplicate_rows,
        "eligible_annual_rows": len(eligible),
        "excluded_rows": sum(exclusions.values()),
        "exclusions_by_reason": dict(sorted(exclusions.items())),
        "repeated_business_key_rows_removed": repeated_business_keys,
        "groups_with_conflicting_values_across_filings": value_conflict_groups,
        "final_rows": len(cleaned),
        "unique_record_ids": len(set(ids)),
        "date_conversion_failures": len(conversion_failures),
        "conversion_failure_details": conversion_failures,
        "missing_before": {
            field: sum(row.get(field, "") in (None, "") for row in rows)
            for field in ["period_start", "period_end", "value", "accession_number", "filed_date", "frame"]
        },
        "missing_after": {
            field: sum(row.get(field, "") in (None, "") for row in cleaned)
            for field in OUTPUT_FIELDS
        },
        "cleaning_rules": [
            "Select six IFRS concepts relevant to growth, profitability, cash generation, and liquidity.",
            "Keep annual Form 20-F facts with fiscal period FY, EUR units, and a December 31 period end.",
            "Require duration facts to span 365 or 366 days; instant cash facts legitimately have no start date.",
            "For repeated metric/year/unit keys, retain the observation from the latest filing date.",
            "Preserve negative profit values because losses are valid, not errors.",
            "Standardize metric names to snake_case and units/forms to uppercase.",
        ],
    }
    return cleaned, audit_summary, audit


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"Refusing to write empty output: {path}")
    selected_fields = fields or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=selected_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def create_record_checks(cleaned: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {row["record_id"]: row for row in cleaned}
    planned = [
        ("2017-net_profit_loss-eur", -1235000000, "negative loss must be preserved"),
        ("2021-operating_profit_loss-eur", 94000000, "first positive operating result in the series"),
        ("2022-operating_cash_flow-eur", 46000000, "unusually low but valid positive cash flow"),
        ("2024-cash_and_cash_equivalents-eur", 4781000000, "instant fact has no period_start"),
        ("2025-revenue-eur", 17186000000, "latest annual revenue and single filing context"),
    ]
    checks = []
    for record_id, expected, reason in planned:
        actual_row = by_id.get(record_id, {})
        actual = actual_row.get("value_eur")
        checks.append(
            {
                "record_id": record_id,
                "original_value": actual,
                "expected_value": expected,
                "actual_value": actual,
                "reason": reason,
                "matches": actual == expected,
                "source_accession": actual_row.get("accession_number", "MISSING"),
            }
        )
    return checks


def create_year_summary(cleaned: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create a compact analysis table with transparent denominators."""
    by_year: dict[int, dict[str, Any]] = defaultdict(dict)
    for row in cleaned:
        if row["calendar_year"] >= 2016:
            by_year[row["calendar_year"]][row["metric"]] = row["value_eur"]
    result: list[dict[str, Any]] = []
    previous_revenue: int | float | None = None
    for year, values in sorted(by_year.items()):
        revenue = values.get("revenue")
        gross_profit = values.get("gross_profit")
        operating_result = values.get("operating_profit_loss")
        row = {"calendar_year": year, **values}
        row["gross_margin_pct"] = round(100 * gross_profit / revenue, 2) if revenue and gross_profit is not None else ""
        row["operating_margin_pct"] = (
            round(100 * operating_result / revenue, 2) if revenue and operating_result is not None else ""
        )
        row["revenue_yoy_pct"] = (
            round(100 * (revenue / previous_revenue - 1), 2) if revenue and previous_revenue else ""
        )
        row["metric_value_count"] = len(values)
        result.append(row)
        previous_revenue = revenue
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()
    input_path = args.input.resolve()
    document = json.loads(input_path.read_text(encoding="utf-8"))
    if document.get("cik") != 1639920 or document.get("entityName") != "Spotify Technology S.A.":
        raise ValueError("Input does not identify Spotify Technology S.A. (CIK 1639920)")

    selected = flatten_selected_facts(document)
    cleaned, summary, audit = clean(selected)
    summary.update(
        {
            "source_file": input_path.name,
            "source_sha256": sha256(input_path),
            "entity_name": document["entityName"],
            "cik": document["cik"],
            "year_range": [min(r["calendar_year"] for r in cleaned), max(r["calendar_year"] for r in cleaned)],
            "metric_count": len({r["metric"] for r in cleaned}),
        }
    )

    write_csv(PROJECT_ROOT / "data" / "interim" / "selected_facts_all_filings.csv", selected)
    write_csv(PROJECT_ROOT / "data" / "processed" / "spotify_annual_financials_clean.csv", cleaned, OUTPUT_FIELDS)
    year_summary = create_year_summary(cleaned)
    write_csv(
        PROJECT_ROOT / "data" / "processed" / "spotify_year_summary.csv",
        year_summary,
        [
            "calendar_year",
            "revenue",
            "gross_profit",
            "operating_profit_loss",
            "net_profit_loss",
            "operating_cash_flow",
            "cash_and_cash_equivalents",
            "gross_margin_pct",
            "operating_margin_pct",
            "revenue_yoy_pct",
            "metric_value_count",
        ],
    )
    # Guarantee all five predeclared difficult cases, then fill the remaining slots
    # with the most recent records. Sort the result for stable human review.
    required_sample_ids = {
        "2017-net_profit_loss-eur",
        "2021-operating_profit_loss-eur",
        "2022-operating_cash_flow-eur",
        "2024-cash_and_cash_equivalents-eur",
        "2025-revenue-eur",
    }
    required_sample = [r for r in cleaned if r["record_id"] in required_sample_ids]
    recent_other = sorted(
        (r for r in cleaned if r["record_id"] not in required_sample_ids),
        key=lambda r: (r["calendar_year"], r["metric"]),
        reverse=True,
    )[: 50 - len(required_sample)]
    sample = sorted(required_sample + recent_other, key=lambda r: (r["calendar_year"], r["metric"]))
    write_csv(PROJECT_ROOT / "data" / "sample" / "spotify_clean_sample_50.csv", sample, OUTPUT_FIELDS)
    write_csv(PROJECT_ROOT / "reports" / "deduplication_audit.csv", audit)
    checks = create_record_checks(cleaned)
    write_csv(PROJECT_ROOT / "reports" / "five_record_checks.csv", checks)
    if not all(row["matches"] for row in checks):
        raise AssertionError("At least one planned record check failed")
    report_path = PROJECT_ROOT / "reports" / "cleaning_audit.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
