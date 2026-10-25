"""Read-only Kalshi market discovery and indicative quote-quality report."""
import datetime as dt
import json
import pathlib
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
BASE = 'https://external-api.kalshi.com/trade-api/v2/markets'
MAX_PAGES = 12
PAGE_SIZE = 100


def cents(value):
    try:
        number = float(value)
        return round(number * 100, 2) if 0 <= number <= 1 else None
    except (ValueError, TypeError):
        return None


def fetch_page(cursor=None):
    params = {'status': 'open', 'limit': PAGE_SIZE}
    if cursor:
        params['cursor'] = cursor
    url = BASE + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        'User-Agent': 'ProjectOutlierResearch/0.3',
        'Accept': 'application/json',
    })
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def scan():
    markets = []
    cursor = None
    seen_cursors = set()
    for page in range(MAX_PAGES):
        data = fetch_page(cursor)
        batch = data.get('markets')
        if not isinstance(batch, list):
            raise ValueError('Unexpected Kalshi response: missing markets list')
        markets.extend(batch)
        next_cursor = data.get('cursor')
        print(f'Page {page + 1}: {len(batch)} markets, total {len(markets)}')
        if not next_cursor or next_cursor in seen_cursors or not batch:
            break
        seen_cursors.add(next_cursor)
        cursor = next_cursor
        time.sleep(0.25)
    return markets


def analyze(markets):
    rows = []
    seen = set()
    for m in markets:
        ticker = m.get('ticker')
        if not ticker or ticker in seen:
            continue
        seen.add(ticker)
        title = m.get('title') or ''
        # Exclude explicitly cross-category combination contracts.
        if 'CROSSCATEGORY' in ticker.upper() or title.lower().count('yes ') >= 3:
            continue
        yb = cents(m.get('yes_bid_dollars'))
        nb = cents(m.get('no_bid_dollars'))
        if yb is None or nb is None:
            continue
        # For a binary contract, opposing bid implies a potential ask price.
        # These are indicative only, NOT verified executable asks.
        implied_yes_ask = round(100 - nb, 2)
        implied_no_ask = round(100 - yb, 2)
        yes_spread = round(implied_yes_ask - yb, 2)
        no_spread = round(implied_no_ask - nb, 2)
        if not (0 < yb < 100 and 0 < nb < 100):
            continue
        if yes_spread < 0 or no_spread < 0:
            continue
        rows.append({
            'ticker': ticker,
            'title': title,
            'yes_bid_cents': yb,
            'no_bid_cents': nb,
            'implied_yes_ask_cents': implied_yes_ask,
            'implied_no_ask_cents': implied_no_ask,
            'indicative_spread_cents': yes_spread,
            'close_time': m.get('close_time'),
            'volume': m.get('volume'),
            'open_interest': m.get('open_interest'),
        })
    rows.sort(key=lambda r: (r['indicative_spread_cents'], -(float(r['volume'] or 0))))
    return rows


def main():
    markets = scan()
    candidates = analyze(markets)
    out = ROOT / 'reports'
    out.mkdir(exist_ok=True)
    snapshot = {
        'source': 'Kalshi public market listings',
        'retrieved_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'raw_market_count': len(markets),
        'filtered_quote_count': len(candidates),
        'disclaimer': 'Indicative bid-derived spreads only; no order book depth, fees, or execution verified.',
        'candidates': candidates,
    }
    (out / 'market_scan.json').write_text(json.dumps(snapshot, indent=2))
    lines = [
        '# Project Outlier v0.3: Read-only market scan', '',
        f"Retrieved: {snapshot['retrieved_at_utc']}",
        f"Raw market records: {len(markets)}",
        f"Filtered quote candidates: {len(candidates)}", '',
        '**Not an arbitrage report.** Opposing bids imply potential asks, but are not executable quotes.',
        'Order-book depth, fees, contract equivalence, and liquidity remain unverified.', '',
        '| Ticker | YES bid | NO bid | Implied YES ask | Spread |',
        '|---|---:|---:|---:|---:|',
    ]
    for r in candidates[:30]:
        lines.append(f"| {r['ticker']} | {r['yes_bid_cents']:.2f}¢ | {r['no_bid_cents']:.2f}¢ | {r['implied_yes_ask_cents']:.2f}¢ | {r['indicative_spread_cents']:.2f}¢ |")
    if not candidates:
        lines.append('| No candidates met the initial filter | | | | |')
    (out / 'market_scan.md').write_text('\n'.join(lines) + '\n')
    print(f'Scan complete: {len(markets)} records, {len(candidates)} filtered candidates')


if __name__ == '__main__':
    main()
