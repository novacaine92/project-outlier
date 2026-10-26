import unittest
from stock_research import load_universe


class UniverseTests(unittest.TestCase):
    def test_diversified_universe(self):
        universe = load_universe()
        tickers = [ticker for ticker, _ in universe]
        sectors = {sector for _, sector in universe}
        self.assertGreaterEqual(len(tickers), 100)
        self.assertEqual(len(tickers), len(set(tickers)))
        self.assertGreaterEqual(len(sectors), 8)
        self.assertIn("MU", tickers)
        self.assertIn("CAT", tickers)


if __name__ == "__main__":
    unittest.main()
