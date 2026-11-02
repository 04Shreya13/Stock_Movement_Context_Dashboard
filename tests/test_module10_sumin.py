import pandas as pd

from dso576_python.analysis import flagged_days, news_context


def test_period_filter_preserves_existing_flags():
    # Business rule: changing the period must not recalculate flags.

    context = pd.DataFrame({
        "symbol": ["AAPL", "AAPL", "AAPL"],
        "date": pd.to_datetime([
            "2024-12-30",
            "2025-01-02",
            "2025-01-03"
        ]),
        "daily_range_pct": [0.02, 0.15, 0.03],
        "is_flagged": [False, True, False],
        "co_flag_count": [0, 1, 0]
    })

    result = flagged_days(context, 2025, "AAPL")

    assert len(result) == 1
    assert result.iloc[0]["date"] == pd.Timestamp("2025-01-02")
    assert result.iloc[0]["daily_range_pct"] == 0.15



def test_news_window_includes_boundary_and_excludes_future():
    news = pd.DataFrame({
        "id": [1, 2, 3, 4],
        "symbol": ["AAPL", "AAPL", "AAPL", "AAPL"],
        "date": pd.to_datetime([
            "2025-01-01",
            "2025-01-02",
            "2025-01-09",
            "2025-01-10"
        ]),
        "highlights": ["a", "b", "c", "d"],
        "highlights_low_info": [True, True, True, True]
    })

    result = news_context(news, "AAPL", "2025-01-09")

    assert len(result) == 2
    assert set(result["date"]) == {
        pd.Timestamp("2025-01-02"),
        pd.Timestamp("2025-01-09")
    }