"""Reproduce Haley Wong's Module 9 feature and number audit.

This check intentionally does not import the dashboard's calculation functions.
It recomputes the audited number directly from the canonical price columns.
"""
from pathlib import Path
from zipfile import ZipFile

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "SHARE_DASHBOARD.zip"
PRICES = ROOT / "data" / "cleaned" / "prices.parquet"
CONTEXT = ROOT / "data" / "cleaned" / "price_context.parquet"


def check_dashboard_package() -> None:
    """Confirm whether imports used by the packaged app are packaged correctly."""
    with ZipFile(ARCHIVE) as archive:
        files = set(archive.namelist())

    root_chart = "SHARE_DASHBOARD/charts.py"
    imported_chart = "SHARE_DASHBOARD/dso576_python/charts.py"
    imported_cleaning = "SHARE_DASHBOARD/dso576_python/cleaning.py"

    print("Feature check: packaged flagged-day workflow")
    print(f"  {root_chart} present: {root_chart in files}")
    print(f"  {imported_chart} present: {imported_chart in files}")
    print(f"  {imported_cleaning} present: {imported_cleaning in files}")
    assert root_chart in files
    assert imported_chart not in files
    assert imported_cleaning not in files


def check_daily_range() -> None:
    """Independently recompute daily range and the AAPL flag threshold."""
    prices = pd.read_parquet(PRICES)
    context = pd.read_parquet(CONTEXT)
    aapl = prices.loc[prices["symbol"].eq("AAPL")].copy()
    aapl["audit_range"] = (aapl["high"] - aapl["low"]) / aapl["close"]

    differences = (aapl["audit_range"] - aapl["daily_range_pct"]).abs()
    threshold = aapl["audit_range"].quantile(0.95)
    recomputed_flags = aapl["audit_range"].ge(threshold)
    stored_flags = context.loc[context["symbol"].eq("AAPL"), "is_flagged"]

    day = aapl.loc[aapl["date"].eq(pd.Timestamp("2025-04-09"))].iloc[0]
    print("Number check: AAPL on 2025-04-09")
    print(f"  high: {day['high']:.8f}")
    print(f"  low: {day['low']:.8f}")
    print(f"  close: {day['close']:.8f}")
    print(f"  independently computed daily range: {day['audit_range']:.10%}")
    print(f"  stored daily range: {day['daily_range_pct']:.10%}")
    print(f"  full-sample AAPL 95th percentile: {threshold:.10%}")
    print(f"  recomputed AAPL flags: {int(recomputed_flags.sum())}")
    print(f"  stored AAPL flags: {int(stored_flags.sum())}")
    print(f"  maximum absolute difference across AAPL rows: {differences.max():.12g}")

    assert len(aapl) == 332
    assert differences.lt(1e-12).all()
    assert int(recomputed_flags.sum()) == 17
    assert int(stored_flags.sum()) == 17


if __name__ == "__main__":
    check_dashboard_package()
    check_daily_range()
    print("Audit checks passed.")
