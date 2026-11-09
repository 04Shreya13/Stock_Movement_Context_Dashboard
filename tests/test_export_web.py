"""Checks that web/data.js says exactly what the tested backend says.

These use the committed canonical data, so they check the real numbers.
"""
import json
import unittest
from pathlib import Path

from dso576_python.analysis import filing_age_days, filing_context, news_context
from dso576_python.constants import COMPANIES
from dso576_python.data_loader import load_cleaned
from dso576_python.export_web import OUTPUT_FILE, build_web_data


class WebDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_cleaned()
        cls.web = build_web_data(cls.data)

    def find_day(self, symbol, date):
        for day in self.web['days'][symbol]:
            if day['date'] == date:
                return day
        self.fail(f'{symbol} {date} not found')

    def test_seventeen_flags_per_company_and_136_in_total(self):
        total = 0
        for symbol in COMPANIES:
            flags = [day for day in self.web['days'][symbol] if day['is_flagged']]
            self.assertEqual(len(flags), 17)
            total += len(flags)
        self.assertEqual(total, 136)

    def test_opening_view(self):
        self.assertEqual(self.web['flagged']['full']['AAPL'][0], '2025-04-09')
        day = self.find_day('AAPL', '2025-04-09')
        self.assertEqual(round(day['daily_range_pct'] * 100, 2), 14.44)
        self.assertEqual(day['co_flag_count'], 8)

    def test_no_flags_case_is_empty(self):
        self.assertEqual(self.web['flagged']['2026']['NVDA'], [])

    def test_indexed_prices_start_at_100(self):
        for period in self.web['periods']:
            for symbol in COMPANIES:
                first = self.web['indexed'][period]['series'][symbol]['indexed'][0]
                self.assertAlmostEqual(first, 100)

    def test_news_and_filing_links_match_the_backend(self):
        for symbol, date in [('AAPL', '2025-04-09'), ('TSLA', '2024-12-18'), ('NVDA', '2025-02-26')]:
            day = self.find_day(symbol, date)
            news_ids = news_context(self.data['news'], symbol, date)['id'].tolist()
            self.assertEqual(day['news_ids'], news_ids)
            filing = filing_context(self.data['filings'], symbol, date)['filing']
            self.assertEqual(day['filing_id'], filing['id'])
            self.assertEqual(day['filing_age_days'], filing_age_days(filing['date'], date))

    def test_filing_age_counts_calendar_days(self):
        self.assertEqual(filing_age_days('2025-01-31', '2025-04-09'), 68)
        self.assertEqual(filing_age_days('2025-08-01', '2025-08-01'), 0)

    def test_committed_file_is_up_to_date(self):
        text = Path(OUTPUT_FILE).read_text(encoding='utf-8')
        saved = json.loads(text.removeprefix('window.STOCK_DATA=').rstrip().rstrip(';'))
        # Compare through JSON so both sides use the same plain types
        built = json.loads(json.dumps(self.web, ensure_ascii=False))
        self.assertEqual(saved, built)


if __name__ == '__main__':
    unittest.main()
