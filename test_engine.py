import unittest
from engine import load_observations, scout, quant, skeptic

class EngineTests(unittest.TestCase):
    def test_data(self):
        self.assertEqual(len(load_observations()), 3)
    def test_scoring(self):
        items = scout(load_observations())
        self.assertEqual(items[0]['event'].split(': ')[1], 'Central bank decision scenario A')
        self.assertAlmostEqual(quant(items[0])['estimated_net_spread'], .04)
    def test_safety_gate(self):
        item = load_observations()[0]
        self.assertGreaterEqual(len(skeptic(item, quant(item))), 4)

if __name__ == '__main__':
    unittest.main()
