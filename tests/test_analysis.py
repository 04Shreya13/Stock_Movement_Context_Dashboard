"""Synthetic fixtures verify logic only; they are NOT submission data."""
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from dso576_python.analysis import (COMPANIES, year_coverage, year_summary, indexed_prices,
    flagged_days, initial_date, news_context, filing_context, date_comparison)
from dso576_python.cleaning import clean_all, build_price_context
from dso576_python.data_loader import validate_data, load_cleaned


def fixture():
    days = pd.to_datetime(['2024-12-30', '2024-12-31', '2025-01-02', '2025-01-03', '2026-01-02'])
    rows, news, filings = [], [], []
    for j, symbol in enumerate(COMPANIES):
        for i, date in enumerate(days):
            close = 100.0 + i * 10 + j
            width = [2, 4, 30, 3, 1][i]
            rows.append(dict(id=len(rows)+1, symbol=symbol, date=date, open=close,
                             high=close + width, low=close - width, close=close,
                             adj_close=close / 2, volume=1000))
        for date in pd.date_range('2024-12-24', '2025-01-04'):
            news.append(dict(id=len(news)+1, symbol=symbol, date=date, highlights='x' * 400))
        for date, form, risk in [('2024-11-01', '10-K', 'annual ' * 400),
                                 ('2025-01-02', '10-Q', 'See annual report'),
                                 ('2025-01-04', '10-Q', 'future ' * 400)]:
            filings.append(dict(id=len(filings)+1, symbol=symbol, date=pd.Timestamp(date),
                                document_type=form, mda_content='Company MD&A', risk_content=risk))
    data, _ = clean_all({name: pd.DataFrame(records) for name, records in
                         [('prices', rows), ('news', news), ('filings', filings)]})
    data['price_context'] = build_price_context(data)
    return data


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.data = fixture()
        self.p, self.c = self.data['prices'], self.data['price_context']

    def test_index_and_summary_use_adjusted_prices(self):
        # Raw close rises while adjusted close falls; metric must use adj_close.
        self.p.loc[(self.p.symbol == 'AAPL') & (self.p.date == '2025-01-03'), 'adj_close'] = 50
        series = indexed_prices(self.p, 2025)
        self.assertTrue(series.groupby('symbol').first().indexed_price.eq(100).all())
        summary = year_summary(self.p, self.c, 2025).set_index('symbol')
        self.assertAlmostEqual(summary.loc['AAPL', 'period_change'], 50/60-1)
        self.assertEqual(summary.loc['AAPL', 'last_close'], 130)
        self.assertEqual(summary.loc['AAPL', 'trading_days'], 2)

    def test_flags_preserved_and_cross_stock_unfiltered(self):
        result = flagged_days(self.c, 2025, 'AAPL')
        self.assertEqual(len(result), 1)
        self.assertEqual(initial_date(self.c, 2025), pd.Timestamp('2025-01-02'))
        self.assertEqual(int(result.iloc[0].co_flag_count), 8)
        self.assertEqual(len(date_comparison(self.c, '2025-01-02')), 8)
        self.assertIsNone(initial_date(self.c, 2026))

    def test_news_inclusive_cross_year_window_no_future(self):
        result = news_context(self.data['news'], 'AAPL', '2025-01-02')
        self.assertEqual(len(result), 8)
        self.assertEqual(result.date.min(), pd.Timestamp('2024-12-26'))
        self.assertEqual(result.date.max(), pd.Timestamp('2025-01-02'))
        self.assertEqual(set(result.symbol), {'AAPL'})

    def test_filing_asof_same_day_and_annual_fallback(self):
        result = filing_context(self.data['filings'], 'AAPL', '2025-01-02')
        self.assertTrue(result['filed_same_day'])
        self.assertEqual(result['filing']['document_type'], '10-Q')
        self.assertEqual(result['annual_risk_fallback']['date'], pd.Timestamp('2024-11-01'))
        self.assertEqual(filing_context(self.data['filings'], 'AAPL', '2024-12-31')['filing']['document_type'], '10-K')
        self.assertIsNone(filing_context(self.data['filings'], 'AAPL', '2020-01-01')['filing'])

    def test_validation_detects_corrupted_context(self):
        self.assertTrue(validate_data(self.data, strict_source=False)['validated'])
        self.c.loc[0, 'co_flag_count'] = 7
        with self.assertRaisesRegex(ValueError, 'co-flag'):
            validate_data(self.data, strict_source=False)

    def test_future_link_and_duplicates_rejected(self):
        self.c.loc[0, 'filing_date'] = pd.Timestamp('2030-01-01')
        with self.assertRaisesRegex(ValueError, 'temporal'):
            validate_data(self.data, strict_source=False)
        self.data = fixture()
        self.data['prices'] = pd.concat([self.data['prices'], self.data['prices'].iloc[[0]]])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            validate_data(self.data, strict_source=False)

    def test_parquet_round_trip_and_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                load_cleaned(tmp)
            for name, frame in self.data.items():
                frame.to_parquet(Path(tmp) / f'{name}.parquet', index=False)
            loaded = load_cleaned(tmp, strict_source=False)
            self.assertEqual(len(loaded['prices']), 40)
            with self.assertRaisesRegex(ValueError, 'dimensions'):
                load_cleaned(tmp)

    def test_no_input_mutation_and_empty_states(self):
        before = self.p.copy(deep=True)
        indexed_prices(self.p, 2025)
        pd.testing.assert_frame_equal(before, self.p)
        self.assertTrue(news_context(self.data['news'], 'AAPL', '2020-01-01').empty)
        self.assertTrue(date_comparison(self.c, '2020-01-01')['is_flagged'].isna().all())
        with self.assertRaises(ValueError):
            indexed_prices(self.p, 2023)
        with self.assertRaises(ValueError):
            flagged_days(self.c, 2025, 'BAD')

    def test_flag_order_ties_break_by_earliest_date(self):
        small = self.c.loc[self.c.symbol.eq('AAPL') & self.c.date.dt.year.eq(2025)].copy()
        small['is_flagged'] = True
        small['daily_range_pct'] = .5
        result = flagged_days(small, 2025, 'AAPL')
        self.assertTrue(result.date.is_monotonic_increasing)


    def test_full_range_period_keeps_all_years(self):
        # 'full' is the default period: it spans every year in the data
        full = flagged_days(self.c, 'full', 'AAPL')
        self.assertEqual(len(full), int(self.c.loc[self.c.symbol.eq('AAPL'), 'is_flagged'].sum()))
        self.assertEqual(year_summary(self.p, self.c, 'full').set_index('symbol').loc['AAPL', 'trading_days'], 5)
        self.assertEqual(indexed_prices(self.p, 'full').groupby('symbol').indexed_price.first().eq(100).all(), True)
        self.assertEqual(year_coverage(self.p, 'full')['coverage_label'], 'Full available range')
        with self.assertRaises(ValueError):
            flagged_days(self.c, 'everything', 'AAPL')

    def test_ticker_list_defined_consistently(self):
        from dso576_python.cleaning import TICKERS
        self.assertEqual(TICKERS, set(COMPANIES))


if __name__ == '__main__':
    unittest.main()
