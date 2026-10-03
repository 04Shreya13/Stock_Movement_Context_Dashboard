"""Reproducible inspection, cleaning, and validation for the three project tables.

Run from any directory with:
    python cleaning_scripts.py

The script preserves the supplied Parquet files and writes derived files to
./outputs. It currently converts date columns to pandas datetime values. It
does not drop rows, fill values, normalize source text, or choose a movement
flagging threshold.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd


TABLES = ("prices", "news", "filings")
KEYS = {
    "prices": ["symbol", "date"],
    "news": ["symbol", "date"],
    "filings": ["symbol", "date", "document_type"],
}
TEXT_COLUMNS = {
    "prices": [],
    "news": ["highlights"],
    "filings": ["document_type", "mda_content", "risk_content"],
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _date_range(series: pd.Series) -> dict[str, str | None]:
    valid = series.dropna()
    if valid.empty:
        return {"minimum": None, "maximum": None}
    return {"minimum": str(valid.min().date()), "maximum": str(valid.max().date())}


def _text_checks(df: pd.DataFrame, name: str) -> dict[str, dict[str, int | float | None]]:
    checks: dict[str, dict[str, int | float | None]] = {}
    for column in TEXT_COLUMNS[name]:
        values = df[column].astype("string")
        lengths = values.str.len()
        checks[column] = {
            "empty_or_whitespace_only": int(values.str.strip().eq("").sum()),
            "leading_or_trailing_whitespace": int(values.ne(values.str.strip()).sum()),
            "minimum_length": int(lengths.min()) if lengths.notna().any() else None,
            "median_length": float(lengths.median()) if lengths.notna().any() else None,
            "maximum_length": int(lengths.max()) if lengths.notna().any() else None,
        }
    return checks


def _profile(df: pd.DataFrame, name: str, source: Path) -> dict[str, Any]:
    parsed_dates = pd.to_datetime(df["date"], errors="coerce")
    key = KEYS[name]
    symbols = df["symbol"].astype("string")
    profile: dict[str, Any] = {
        "source_file": str(Path("data") / source.name),
        "source_sha256": _sha256(source),
        "rows": int(len(df)),
        "columns": list(df.columns),
        "dtypes_before": {column: str(dtype) for column, dtype in df.dtypes.items()},
        "date_conversion_failures": int(parsed_dates.isna().sum()),
        "date_range": _date_range(parsed_dates),
        "nulls_by_column": {column: int(count) for column, count in df.isna().sum().items()},
        "exact_duplicate_rows": int(df.duplicated().sum()),
        "duplicate_ids": int(df["id"].duplicated().sum()),
        "candidate_key": key,
        "duplicate_candidate_keys": int(df.duplicated(key).sum()),
        "symbol_values": sorted(symbols.dropna().unique().tolist()),
        "symbols_with_surrounding_whitespace": int(symbols.ne(symbols.str.strip()).sum()),
        "symbols_not_uppercase": int(symbols.ne(symbols.str.upper()).sum()),
        "rows_by_symbol": {str(k): int(v) for k, v in df.groupby("symbol", dropna=False).size().items()},
        "text_checks": _text_checks(df, name),
    }
    if name == "filings":
        profile["document_type_counts"] = {
            str(k): int(v) for k, v in df["document_type"].value_counts(dropna=False).items()
        }
        profile["repeated_symbol_date_pairs"] = int(df.duplicated(["symbol", "date"]).sum())
    if name == "prices":
        price_columns = ["open", "high", "low", "close", "adj_close"]
        profile["price_validity"] = {
            "nonpositive_by_column": {column: int((df[column] <= 0).sum()) for column in price_columns},
            "high_below_low": int((df["high"] < df["low"]).sum()),
            "open_outside_low_high": int(((df["open"] < df["low"]) | (df["open"] > df["high"])).sum()),
            "close_outside_low_high": int(((df["close"] < df["low"]) | (df["close"] > df["high"])).sum()),
            "negative_volume": int((df["volume"] < 0).sum()),
        }
    return profile


def _build_filing_lookup(prices: pd.DataFrame, filings: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """For each price date, select the latest same-symbol filing on or before it."""
    rows: list[dict[str, Any]] = []
    valid_filings = filings.dropna(subset=["date"]).copy()
    for price in prices.itertuples(index=False):
        eligible = valid_filings.loc[
            (valid_filings["symbol"] == price.symbol) & (valid_filings["date"] <= price.date)
        ]
        selected = None
        if not eligible.empty:
            selected = eligible.sort_values(["date", "document_type", "id"], kind="stable").iloc[-1]
        rows.append(
            {
                "price_id": price.id,
                "symbol": price.symbol,
                "price_date": price.date,
                "filing_id": None if selected is None else selected["id"],
                "filing_date": pd.NaT if selected is None else selected["date"],
                "document_type": None if selected is None else selected["document_type"],
                "days_since_filing": None
                if selected is None
                else int((price.date - selected["date"]).days),
            }
        )
    lookup = pd.DataFrame(rows)
    matched = lookup["filing_date"].notna()
    report = {
        "price_events_checked": int(len(lookup)),
        "events_with_prior_filing": int(matched.sum()),
        "events_without_prior_filing": int((~matched).sum()),
        "future_filings_selected": int((lookup.loc[matched, "filing_date"] > lookup.loc[matched, "price_date"]).sum()),
        "relationship": "many price dates to one latest prior filing per symbol/date",
    }
    return lookup, report


def _build_news_window_counts(prices: pd.DataFrame, news: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Count calendar-day news from event date back seven days, inclusive."""
    rows: list[dict[str, Any]] = []
    grouped_news = {symbol: group for symbol, group in news.dropna(subset=["date"]).groupby("symbol")}
    for price in prices.itertuples(index=False):
        company_news = grouped_news.get(price.symbol)
        if company_news is None:
            count = 0
        else:
            lower_bound = price.date - pd.Timedelta(days=7)
            count = int(((company_news["date"] >= lower_bound) & (company_news["date"] <= price.date)).sum())
        rows.append(
            {
                "price_id": price.id,
                "symbol": price.symbol,
                "price_date": price.date,
                "window_start": price.date - pd.Timedelta(days=7),
                "window_end": price.date,
                "news_record_count": count,
            }
        )
    counts = pd.DataFrame(rows)
    report = {
        "price_events_checked": int(len(counts)),
        "window_definition": "same symbol, from event date minus 7 calendar days through event date, inclusive",
        "events_with_no_news": int(counts["news_record_count"].eq(0).sum()),
        "minimum_news_records_per_event": int(counts["news_record_count"].min()) if len(counts) else 0,
        "median_news_records_per_event": float(counts["news_record_count"].median()) if len(counts) else 0.0,
        "maximum_news_records_per_event": int(counts["news_record_count"].max()) if len(counts) else 0,
    }
    return counts, report


def _build_price_metrics(prices: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    metrics = prices[["id", "symbol", "date", "high", "low", "close"]].copy()
    metrics["daily_range"] = metrics["high"] - metrics["low"]
    metrics["normalized_range"] = metrics["daily_range"] / metrics["close"]
    per_symbol = metrics.groupby("symbol")["normalized_range"].agg(["count", "min", "mean", "max"])
    report = {
        "definition_raw": "high - low",
        "definition_normalized": "(high - low) / close",
        "flag_threshold_applied": False,
        "reason_threshold_not_applied": "The project description presents both a configurable raw threshold and a top-5%-normalized example; user decision is pending.",
        "record_count": int(len(metrics)),
        "record_count_by_symbol": {str(k): int(v) for k, v in metrics.groupby("symbol").size().items()},
        "missing_group_keys": int(metrics["symbol"].isna().sum()),
        "missing_metric_values": int(metrics[["daily_range", "normalized_range"]].isna().sum().sum()),
        "non_finite_metric_values": int(metrics[["daily_range", "normalized_range"]].isin([float("inf"), float("-inf")]).sum().sum()),
        "normalized_range_by_symbol": {
            str(symbol): {
                "record_count": int(row["count"]),
                "minimum": float(row["min"]),
                "mean": float(row["mean"]),
                "maximum": float(row["max"]),
            }
            for symbol, row in per_symbol.iterrows()
        },
    }
    return metrics, report


def _build_record_checks(
    raw: dict[str, pd.DataFrame],
    cleaned: dict[str, pd.DataFrame],
    metrics: pd.DataFrame,
    news_windows: pd.DataFrame,
    filing_lookup: pd.DataFrame,
) -> pd.DataFrame:
    """Run five pre-specified record checks, including non-trading and extreme cases."""
    records: list[dict[str, Any]] = []

    # 1: ordinary price row. Expected before comparison: original values are retained;
    # only the date representation changes to pandas datetime.
    source = raw["prices"].loc[(raw["prices"].symbol == "AAPL") & (raw["prices"].date.astype(str) == "2024-12-02")].iloc[0]
    actual = cleaned["prices"].loc[cleaned["prices"].id == source["id"]].iloc[0]
    fields = ["symbol", "open", "high", "low", "close", "adj_close", "volume"]
    expected_ok = all(source[field] == actual[field] for field in fields)
    records.append({
        "check_id": 1, "table": "prices", "record": "AAPL 2024-12-02",
        "difficulty": "ordinary price row",
        "expected_before_check": "Source price values are unchanged; date is valid and unique by symbol/date.",
        "actual": f"date={actual['date'].date()}, values_preserved={expected_ok}, symbol-date duplicates={int(cleaned['prices'].duplicated(['symbol','date']).sum())}",
        "matches_expectation": bool(expected_ok and cleaned["prices"].duplicated(["symbol", "date"]).sum() == 0),
    })

    # 2: most volatile observed row, selected deterministically from source-derived metrics.
    extreme = metrics.sort_values("normalized_range", kind="stable").iloc[-1]
    original_extreme = raw["prices"].loc[raw["prices"].id == extreme["id"]].iloc[0]
    formula_ok = (
        abs(float(extreme["daily_range"]) - float(original_extreme["high"] - original_extreme["low"])) < 1e-10
        and abs(float(extreme["normalized_range"]) - float(extreme["daily_range"] / original_extreme["close"])) < 1e-10
    )
    records.append({
        "check_id": 2, "table": "prices", "record": f"{extreme['symbol']} {extreme['date'].date()}",
        "difficulty": "largest normalized daily range in this dataset",
        "expected_before_check": "Derived range equals high minus low; normalized range equals range divided by close.",
        "actual": f"daily_range={float(extreme['daily_range']):.8f}, normalized_range={float(extreme['normalized_range']):.10f}, formulas_match={formula_ok}",
        "matches_expectation": bool(formula_ok),
    })

    # 3: news on a calendar day without a same-day trading row must remain available.
    news_record = raw["news"].loc[(raw["news"].symbol == "AAPL") & (raw["news"].date.astype(str) == "2024-12-01")].iloc[0]
    cleaned_news_record = cleaned["news"].loc[cleaned["news"].id == news_record["id"]].iloc[0]
    same_day_price_exists = bool(
        ((cleaned["prices"].symbol == "AAPL") & (cleaned["prices"].date == cleaned_news_record["date"])).any()
    )
    no_same_day_price = not same_day_price_exists
    news_text_preserved = news_record["highlights"] == cleaned_news_record["highlights"]
    records.append({
        "check_id": 3, "table": "news", "record": "AAPL 2024-12-01",
        "difficulty": "calendar-day news date without same-day price",
        "expected_before_check": "Retain the news row and text even though no same-day trading price exists.",
        "actual": f"retained={not cleaned_news_record.empty}, no_same_day_price={no_same_day_price}, text_preserved={news_text_preserved}",
        "matches_expectation": bool(no_same_day_price and news_text_preserved),
    })

    # 4: weekend news is included in the inclusive seven-calendar-day context window.
    weekend = cleaned["news"].loc[(cleaned["news"].symbol == "AAPL") & (cleaned["news"].date.astype(str) == "2024-12-07")]
    event = pd.Timestamp("2024-12-09")
    included = bool(len(weekend) == 1 and event - pd.Timedelta(days=7) <= weekend.iloc[0]["date"] <= event)
    window_count = news_windows.loc[(news_windows.symbol == "AAPL") & (news_windows.price_date == event), "news_record_count"]
    records.append({
        "check_id": 4, "table": "news", "record": "AAPL 2024-12-07 in AAPL 2024-12-09 context",
        "difficulty": "weekend news included in prior-seven-day window",
        "expected_before_check": "AAPL weekend news is retained and falls inside the Dec 2–Dec 9 inclusive context window.",
        "actual": f"weekend_row_retained={len(weekend)==1}, included_in_window={included}, total_window_news={int(window_count.iloc[0]) if len(window_count) else 'no event'}",
        "matches_expectation": bool(included and len(window_count) == 1),
    })

    # 5: latest available filing for ADBE on Mar 31, 2026 must not be from the future.
    event = pd.Timestamp("2026-03-31")
    candidates = raw["filings"].loc[(raw["filings"].symbol == "ADBE") & (pd.to_datetime(raw["filings"].date) <= event)]
    expected_filing_date = pd.to_datetime(candidates["date"]).max()
    selected = filing_lookup.loc[(filing_lookup.symbol == "ADBE") & (filing_lookup.price_date == event)].iloc[0]
    matched_date = pd.Timestamp(selected["filing_date"])
    latest_and_prior = matched_date == expected_filing_date and matched_date <= event
    records.append({
        "check_id": 5, "table": "filings", "record": "ADBE latest filing for price date 2026-03-31",
        "difficulty": "as-of filing lookup at date boundary",
        "expected_before_check": f"Select the latest ADBE filing dated on or before 2026-03-31 ({expected_filing_date.date()}).",
        "actual": f"selected filing date={matched_date.date()}, document_type={selected['document_type']}, latest_and_not_future={latest_and_prior}",
        "matches_expectation": bool(latest_and_prior),
    })
    return pd.DataFrame(records)


def _build_sample(cleaned: dict[str, pd.DataFrame], metrics: pd.DataFrame) -> pd.DataFrame:
    """Create 48 full rows, 16 per table, including difficult cases."""
    parts: list[pd.DataFrame] = []

    price_order = metrics.sort_values("normalized_range", kind="stable")
    for reason, selection in (
        ("lowest normalized daily range", price_order.head(8)["id"]),
        ("highest normalized daily range", price_order.tail(8)["id"]),
    ):
        part = cleaned["prices"].loc[cleaned["prices"].id.isin(selection)].copy()
        part.insert(0, "sample_reason", reason)
        part.insert(0, "source_table", "prices")
        parts.append(part)

    prices_key = cleaned["prices"][["symbol", "date"]].drop_duplicates()
    news_with_price = cleaned["news"].merge(prices_key.assign(_has_price=True), on=["symbol", "date"], how="left")
    unmatched = news_with_price.loc[news_with_price["_has_price"].isna()].head(8)
    matched = news_with_price.loc[news_with_price["_has_price"].notna()]
    if len(matched) > 8:
        matched = matched.iloc[:: max(1, len(matched) // 8)].head(8)
    for reason, selected in (
        ("calendar-day news without same-day price", unmatched),
        ("news on a trading date with same-day price", matched),
    ):
        ids = selected["id"].tolist()
        part = cleaned["news"].loc[cleaned["news"].id.isin(ids)].copy()
        part.insert(0, "sample_reason", reason)
        part.insert(0, "source_table", "news")
        parts.append(part)

    filing_lengths = cleaned["filings"].assign(_risk_length=cleaned["filings"]["risk_content"].astype("string").str.len())
    for reason, selected in (
        ("shortest risk text", filing_lengths.nsmallest(8, "_risk_length")),
        ("longest risk text", filing_lengths.nlargest(8, "_risk_length")),
    ):
        part = cleaned["filings"].loc[cleaned["filings"].id.isin(selected["id"])].copy()
        part.insert(0, "sample_reason", reason)
        part.insert(0, "source_table", "filings")
        parts.append(part)

    sample = pd.concat(parts, ignore_index=True, sort=False)
    if len(sample) > 50:
        raise ValueError(f"Sample has {len(sample)} rows; assignment limit is 50.")
    return sample


def run_cleaning(project_dir: str | Path | None = None, verbose: bool = True) -> dict[str, Any]:
    """Run all checks, preserve rows, convert dates, and write reproducible outputs."""
    root = Path(project_dir).resolve() if project_dir else Path(__file__).resolve().parent
    data_dir = root / "data"
    output_dir = root / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    raw: dict[str, pd.DataFrame] = {}
    cleaned: dict[str, pd.DataFrame] = {}
    profiles: dict[str, Any] = {}
    reconciliation: dict[str, Any] = {}

    for name in TABLES:
        source = data_dir / f"{name}.parquet"
        if not source.is_file():
            raise FileNotFoundError(f"Required input file was not found: {source}")
        original = pd.read_parquet(source)
        if "date" not in original.columns:
            raise KeyError(f"Expected a 'date' column in {source}")
        raw[name] = original.copy()
        profiles[name] = _profile(original, name, source)

        result = original.copy()
        # Invalid dates become NaT and remain in the output for review; rows are not dropped.
        result["date"] = pd.to_datetime(result["date"], errors="coerce")
        cleaned[name] = result
        destination = output_dir / f"{name}_cleaned.parquet"
        result.to_parquet(destination, index=False)
        profiles[name]["dtypes_after"] = {column: str(dtype) for column, dtype in result.dtypes.items()}
        profiles[name]["rows_after"] = int(len(result))
        profiles[name]["nulls_after_by_column"] = {
            column: int(count) for column, count in result.isna().sum().items()
        }
        profiles[name]["candidate_key_duplicates_after"] = int(result.duplicated(KEYS[name]).sum())
        expected_values = original.copy()
        expected_values["date"] = pd.to_datetime(expected_values["date"], errors="coerce")
        profiles[name]["values_preserved_except_date_conversion"] = bool(result.equals(expected_values))
        profiles[name]["output_file"] = str(destination.relative_to(root))
        reconciliation[name] = {
            "rows_before": int(len(original)),
            "rows_after": int(len(result)),
            "rows_removed": int(len(original) - len(result)),
            "row_policy": "No rows are dropped or added; dates are converted and invalid dates, if any, are retained as NaT for review.",
        }

    # Cross-table grain, merge coverage, context windows, and filing as-of checks.
    price_keys = cleaned["prices"][["symbol", "date"]]
    news_price_merge = cleaned["news"].merge(
        price_keys.drop_duplicates().assign(_price_exists=True),
        on=["symbol", "date"], how="left", validate="many_to_one",
    )
    news_alignment = {
        "news_rows_with_same_day_price": int(news_price_merge["_price_exists"].notna().sum()),
        "news_rows_without_same_day_price_retained": int(news_price_merge["_price_exists"].isna().sum()),
        "price_rows_with_same_day_news": int(
            cleaned["prices"].merge(
                cleaned["news"][["symbol", "date"]].drop_duplicates().assign(_news_exists=True),
                on=["symbol", "date"], how="left", validate="one_to_one",
            )["_news_exists"].notna().sum()
        ),
        "relationship_for_same_day_join": "one-to-one on (symbol, date) for current data",
        "policy": "Keep unmatched calendar-day news; do not use an inner join that removes it.",
    }
    news_windows, news_window_report = _build_news_window_counts(cleaned["prices"], cleaned["news"])
    filing_lookup, filing_report = _build_filing_lookup(cleaned["prices"], cleaned["filings"])
    metrics, metric_report = _build_price_metrics(cleaned["prices"])

    # Reconcile price totals and date-typed serialization.
    price_raw = raw["prices"]
    price_clean = cleaned["prices"]
    reconciliation["prices"].update({
        "volume_total_before": int(price_raw["volume"].sum()),
        "volume_total_after": int(price_clean["volume"].sum()),
        "daily_range_total_before": float((price_raw["high"] - price_raw["low"]).sum()),
        "daily_range_total_after": float((price_clean["high"] - price_clean["low"]).sum()),
    })

    # Date coverage by symbol detects unexpected gaps in this daily news table.
    news_calendar_gaps: dict[str, int] = {}
    for symbol, group in cleaned["news"].dropna(subset=["date"]).groupby("symbol"):
        observed = group["date"].nunique()
        expected = int((group["date"].max() - group["date"].min()).days + 1)
        news_calendar_gaps[str(symbol)] = expected - int(observed)

    checks = _build_record_checks(raw, cleaned, metrics, news_windows, filing_lookup)
    sample = _build_sample(cleaned, metrics)

    metrics.to_csv(output_dir / "price_metrics.csv", index=False)
    news_windows.to_csv(output_dir / "news_window_counts.csv", index=False)
    filing_lookup.to_csv(output_dir / "filing_lookup.csv", index=False)
    checks.to_csv(output_dir / "record_checks.csv", index=False)
    sample.to_parquet(output_dir / "data_sample.parquet", index=False)
    sample.to_csv(output_dir / "data_sample.csv", index=False, encoding="utf-8")

    report: dict[str, Any] = {
        "project": "Stock Movement Context Dashboard data preparation",
        "source": {
            "dataset": "TheFinAI/Herculean",
            "url": "https://huggingface.co/datasets/TheFinAI/Herculean",
            "revision_or_download_date": "Not recorded in the supplied project documents; use the SHA-256 values below to identify the provided files.",
        },
        "cleaning_policy": {
            "source_files_modified": False,
            "transformations": ["Convert date columns to datetime; retain invalid parsed dates as NaT for review."],
            "rows_dropped": False,
            "values_filled": False,
            "text_trimmed_or_normalized": False,
            "movement_threshold_applied": False,
        },
        "tables": profiles,
        "row_reconciliation": reconciliation,
        "cross_table_validation": {
            "same_day_news_price": news_alignment,
            "news_calendar_missing_dates_by_symbol": news_calendar_gaps,
            "news_context_window": news_window_report,
            "latest_prior_filing": filing_report,
        },
        "calculation_checks": metric_report,
        "record_check_count": int(len(checks)),
        "record_check_pass_count": int(checks["matches_expectation"].sum()),
        "record_checks_all_pass": bool(checks["matches_expectation"].all()),
        "sample": {
            "file": "outputs/data_sample.parquet",
            "row_count": int(len(sample)),
            "selection": "48 full rows: 16 per table; prices selected from lowest/highest normalized ranges, news selected from matched/unmatched trading dates, filings selected by shortest/longest risk-text length.",
        },
        "expected_user_review": [
            "Choose whether movement flags use raw range, normalized range, or a configurable threshold.",
            "Review the proposed trimming of filing text boundary whitespace before applying it; this run preserves source text exactly.",
        ],
    }
    report_path = output_dir / "cleaning_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")

    if verbose:
        print(f"Cleaning and validation complete. Outputs: {output_dir}")
        for name in TABLES:
            item = profiles[name]
            print(
                f"{name}: {item['rows']} rows; date conversion failures={item['date_conversion_failures']}; "
                f"nulls={sum(item['nulls_by_column'].values())}; exact duplicates={item['exact_duplicate_rows']}"
            )
        print(
            f"news same-day matches={news_alignment['news_rows_with_same_day_price']}; "
            f"unmatched news retained={news_alignment['news_rows_without_same_day_price_retained']}"
        )
        print(
            f"news windows with no news={news_window_report['events_with_no_news']}; "
            f"price events with prior filing={filing_report['events_with_prior_filing']}/{filing_report['price_events_checked']}"
        )
        print(f"record checks passed={report['record_check_pass_count']}/{report['record_check_count']}")
        print(f"sample rows={len(sample)}; report={report_path.relative_to(root)}")
    return report


if __name__ == "__main__":
    run_cleaning()
