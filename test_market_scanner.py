"""Offline tests for the read-only market scanner."""
import unittest
from unittest.mock import patch

import market_scanner as scanner


def market(ticker, yes, no, **kwargs):
    return {
        'ticker': ticker,
        'title': kwargs.pop('title', 'Sample event'),
        'yes_bid_dollars': yes,
        'no_bid_dollars': no,
        **kwargs,
    }


class ScannerTests(unittest.TestCase):
    def test_cents_validation(self):
        self.assertEqual(scanner.cents('0.42'), 42.0)
        self.assertIsNone(scanner.cents('1.01'))
        self.assertIsNone(scanner.cents('-0.01'))
        self.assertIsNone(scanner.cents(None))
        self.assertIsNone(scanner.cents('invalid'))

    def test_bid_derived_spread(self):
        rows = scanner.analyze([market('EXAMPLE', '0.42', '0.55', volume=100)])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['implied_yes_ask_cents'], 45.0)
        self.assertEqual(rows[0]['indicative_spread_cents'], 3.0)

    def test_duplicate_and_combination_exclusions(self):
        rows = scanner.analyze([
            market('ONE', '0.42', '0.55'),
            market('ONE', '0.42', '0.55'),
            market('CROSSCATEGORY-TEST', '0.42', '0.55'),
            market('MANY-YES', '0.42', '0.55', title='yes a yes b yes c'),
        ])
        self.assertEqual([r['ticker'] for r in rows], ['ONE'])

    def test_invalid_and_crossed_quotes_excluded(self):
        rows = scanner.analyze([
            market('ZERO', '0', '0.50'),
            market('MISSING', None, '0.50'),
            market('CROSSED', '0.70', '0.40'),
            market('VALID', '0.40', '0.50'),
        ])
        self.assertEqual([r['ticker'] for r in rows], ['VALID'])

    def test_spread_then_volume_sorting(self):
        rows = scanner.analyze([
            market('WIDE', '0.40', '0.50', volume=100),
            market('SMALL', '0.45', '0.53', volume=10),
            market('LARGE', '0.45', '0.53', volume=200),
        ])
        self.assertEqual([r['ticker'] for r in rows], ['LARGE', 'SMALL', 'WIDE'])

    def test_rejection_diagnostics(self):
        reasons = {}
        rows = scanner.analyze([
            market('CROSSCATEGORY-A', '0.40', '0.50'),
            market('MISSING', None, '0.50'),
            market('ZERO', '0', '0.50'),
            market('CROSSED', '0.70', '0.40'),
            market('GOOD', '0.40', '0.50'),
            market('GOOD', '0.40', '0.50'),
        ], reasons)
        self.assertEqual(len(rows), 1)
        self.assertEqual(reasons['combination_contract'], 1)
        self.assertEqual(reasons['missing_or_invalid_bid'], 1)
        self.assertEqual(reasons['zero_or_boundary_bid'], 1)
        self.assertEqual(reasons['crossed_quote'], 1)
        self.assertEqual(reasons['missing_or_duplicate_ticker'], 1)
        self.assertEqual(reasons['accepted'], 1)

    @patch.object(scanner.time, 'sleep')
    @patch.object(scanner, 'fetch_page')
    def test_pagination(self, fetch, sleep):
        fetch.side_effect = [
            {'markets': [market('A', '0.4', '0.5')], 'cursor': 'next'},
            {'markets': [market('B', '0.4', '0.5')], 'cursor': ''},
        ]
        self.assertEqual(len(scanner.scan()), 2)
        self.assertEqual(fetch.call_count, 2)
        sleep.assert_called_once()


if __name__ == '__main__':
    unittest.main()
