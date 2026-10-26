import unittest
from stock_validation import validate


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{"date": str(i), "open": 100.0, "close": 101.0, "volume": 100} for i in range(100)]

    def test_next_open_not_signal_close(self):
        self.rows[11]["open"] = 110.0
        self.rows[15]["close"] = 120.0
        event = [{"strategy": "oversold_rebound", "index": 10}]
        result = validate(self.rows, event)
        self.assertAlmostEqual(result["strategies"]["oversold_rebound"]["train"]["average_net_return"],
                               120 / 110 - 1 - .002, places=6)

    def test_chronological_split(self):
        events = [{"strategy": "oversold_rebound", "index": i} for i in [10, 60, 70, 80]]
        result = validate(self.rows, events)
        self.assertEqual(result["strategies"]["oversold_rebound"]["train"]["sample_count"], 2)
        self.assertEqual(result["strategies"]["oversold_rebound"]["test"]["sample_count"], 2)

    def test_missing_open_is_not_imputed(self):
        self.rows[11]["open"] = None
        result = validate(self.rows, [{"strategy": "oversold_rebound", "index": 10}])
        self.assertEqual(result["strategies"]["oversold_rebound"]["train"]["sample_count"], 0)


if __name__ == "__main__":
    unittest.main()
