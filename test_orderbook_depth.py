"""Offline tests for the read-only depth sampler."""
import unittest
from orderbook_depth import evaluate, levels


class DepthTests(unittest.TestCase):
    def test_dollar_bid_levels(self):
        book = {"yes_dollars": [["0.40", 5], ["0.42", 3]]}
        self.assertEqual(levels(book, "yes"), [(42.0, 3.0), (40.0, 5.0)])

    def test_depth_and_spread(self):
        result = evaluate({
            "yes_dollars": [["0.42", 3]],
            "no_dollars": [["0.55", 7]],
        })
        self.assertEqual(result["status"], "two_sided_book")
        self.assertEqual(result["spread_cents"], 3.0)
        self.assertEqual(result["implied_yes_ask_contracts"], 7)
        self.assertFalse(result["profitable_trade_verified"])

    def test_missing_side(self):
        self.assertEqual(evaluate({"yes_dollars": [["0.42", 3]], "no_dollars": []})["status"],
                         "insufficient_two_sided_depth")

    def test_crossed_book(self):
        self.assertEqual(evaluate({"yes_dollars": [["0.60", 3]], "no_dollars": [["0.50", 3]]})["status"],
                         "crossed_or_inconsistent_book")

    def test_invalid_levels(self):
        self.assertEqual(levels({"yes_dollars": [["bad", 4], ["0.4", 0], ["0.5", 2]]}, "yes"),
                         [(50.0, 2.0)])


if __name__ == "__main__":
    unittest.main()
