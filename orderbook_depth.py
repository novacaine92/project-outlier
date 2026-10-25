"""Read-only depth sampling for shortlisted Kalshi markets.

Book levels are resting bids, not executable asks. No trades are placed.
"""
import datetime as dt
import json
import pathlib
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
BASE = "https://external-api.kalshi.com/trade-api/v2/markets"
MAX_BOOKS = 12


def levels(book, side):
    """Normalize Kalshi dollar-price bid levels to (cents, contracts)."""
    raw = book.get(side + "_dollars")
    dollar_prices = raw is not None
    if raw is None:
        raw = book.get(side, [])
    if not isinstance(raw, list):
        return []
    result = []
    for entry in raw:
        try:
            price, quantity = entry[:2]
            price = float(price) * (100 if dollar_prices else 1)
            quantity = float(quantity)
            if 0 < price < 100 and quantity > 0:
                result.append((round(price, 2), quantity))
        except (TypeError, ValueError, IndexError):
            continue
    return sorted(result, reverse=True)


def evaluate(book):
    yes = levels(book, "yes")
    no = levels(book, "no")
    if not yes or not no:
        return {"status": "insufficient_two_sided_depth"}
    best_yes, yes_qty = yes[0]
    best_no, no_qty = no[0]
    spread = round(100 - best_no - best_yes, 2)
    if spread < 0:
        return {"status": "crossed_or_inconsistent_book"}
    return {
        "status": "two_sided_book",
        "yes_best_bid_cents": best_yes,
        "yes_best_bid_contracts": yes_qty,
        "no_best_bid_cents": best_no,
        "no_best_bid_contracts": no_qty,
        "implied_yes_ask_cents": round(100 - best_no, 2),
        "implied_yes_ask_contracts": no_qty,
        "spread_cents": spread,
        "fees_included": False,
        "profitable_trade_verified": False,
    }


def fetch_book(ticker):
    url = BASE + "/" + urllib.parse.quote(ticker, safe="") + "/orderbook"
    req = urllib.request.Request(url, headers={
        "User-Agent": "ProjectOutlierResearch/0.5",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=20) as response:
        data = json.load(response)
    return data.get("orderbook", {})


def main():
    report = ROOT / "reports" / "market_scan.json"
    if not report.exists():
        raise FileNotFoundError("Run market_scanner.py first")
    snapshot = json.loads(report.read_text())
    candidates = snapshot.get("candidates", [])
    results = []
    for candidate in candidates[:MAX_BOOKS]:
        ticker = candidate["ticker"]
        try:
            detail = evaluate(fetch_book(ticker))
        except Exception as exc:
            # Retain errors rather than silently treating missing data as zero liquidity.
            detail = {"status": "fetch_error", "error_type": type(exc).__name__}
        results.append({"ticker": ticker, "title": candidate.get("title"), **detail})
        time.sleep(0.15)
    output = {
        "source": "Kalshi public order books",
        "retrieved_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "books_requested": len(results),
        "two_sided_books": sum(x["status"] == "two_sided_book" for x in results),
        "note": "Indicative depth only. No fee-adjusted edge, executable profit, or arbitrage established.",
        "results": results,
    }
    out = ROOT / "reports" / "orderbook_depth.json"
    out.write_text(json.dumps(output, indent=2))
    print(f"Depth sample: {output['two_sided_books']}/{len(results)} two-sided books")


if __name__ == "__main__":
    main()
