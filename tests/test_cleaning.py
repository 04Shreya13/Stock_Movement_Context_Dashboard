import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from clean_spotify_financials import clean, create_record_checks, create_year_summary, flatten_selected_facts


class SpotifyCleaningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = ROOT / "data" / "raw" / "spotify_companyfacts_2026-10-03.json"
        document = json.loads(source.read_text(encoding="utf-8"))
        cls.selected = flatten_selected_facts(document)
        cls.cleaned, cls.audit, cls.dedup = clean(cls.selected)

    def test_expected_counts_and_unique_key(self):
        self.assertEqual(len(self.selected), 152)
        self.assertEqual(len(self.cleaned), 61)
        self.assertEqual(len({r["record_id"] for r in self.cleaned}), 61)
        self.assertEqual(self.audit["repeated_business_key_rows_removed"], 91)

    def test_types_dates_and_units(self):
        self.assertTrue(all(isinstance(r["calendar_year"], int) for r in self.cleaned))
        self.assertTrue(all(isinstance(r["value_eur"], (int, float)) for r in self.cleaned))
        self.assertTrue(all(r["unit"] == "EUR" and r["form"] == "20-F" for r in self.cleaned))
        self.assertTrue(all(r["filed_date"] > r["period_end"] for r in self.cleaned))

    def test_instant_facts_explain_missing_start_dates(self):
        no_start = [r for r in self.cleaned if not r["period_start"]]
        self.assertEqual(len(no_start), 11)
        self.assertTrue(all(r["metric"] == "cash_and_cash_equivalents" for r in no_start))
        self.assertTrue(all(r["fact_type"] == "instant" for r in no_start))

    def test_financial_relationships_and_suspicious_values(self):
        summary = create_year_summary(self.cleaned)
        self.assertTrue(all(r["revenue"] > 0 for r in summary))
        self.assertTrue(all(0 <= r["gross_profit"] <= r["revenue"] for r in summary))
        # Losses are economically plausible and must not be converted to missing/positive.
        self.assertTrue(any(r["net_profit_loss"] < 0 for r in summary))

    def test_five_predeclared_record_checks(self):
        checks = create_record_checks(self.cleaned)
        self.assertEqual(len(checks), 5)
        self.assertTrue(all(r["matches"] for r in checks))


if __name__ == "__main__":
    unittest.main()
