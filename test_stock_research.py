"""Deterministic stock scanner tests, no network required."""
import unittest
from stock_research import signals, summarize, LOOKBACK, HORIZON


class StockResearchTests(unittest.TestCase):
    def test_oversold_signal_and_forward_return(self):
        rows = [{"date": f"day{i}", "close": float(100 + (i % 3)), "volume": 100} for i in range(30)]
        rows[20]["close"] = 80
        events = signals(rows)
        rebound = [e for e in events if e["strategy"] == "oversold_rebound" and e["index"] == 20]
        self.assertEqual(len(rebound), 1)
        self.assertAlmostEqual(rebound[0]["forward_5d_net_return"], 101 / 80 - 1 - .002, places=6)

    def test_momentum_requires_volume(self):
        rows = [{"date": f"day{i}", "close": float(100 + (i % 3)), "volume": 100} for i in range(30)]
        rows[20].update(close=110, volume=200)
        events = signals(rows)
        self.assertTrue(any(e["strategy"] == "momentum_breakout" and e["index"] == 20 for e in events))
        rows[20]["volume"] = 100
        self.assertFalse(any(e["strategy"] == "momentum_breakout" and e["index"] == 20 for e in signals(rows)))

    def test_nonoverlap(self):
        events = [
            {"strategy": "oversold_rebound", "index": i, "date": str(i), "forward_5d_net_return": .01}
            for i in [20, 21, 25, 30]
        ]
        self.assertEqual(summarize(events)["oversold_rebound"]["nonoverlapping_samples"], 3)

    def test_insufficient_bars(self):
        self.assertEqual(signals([{"date": "x", "close": 1, "volume": 1}] * (LOOKBACK + HORIZON)), [])


if __name__ == "__main__":
    unittest.main()
