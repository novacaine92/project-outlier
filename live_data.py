import datetime as dt
import json
import pathlib
import urllib.request

URL = "https://external-api.kalshi.com/trade-api/v2/markets?status=open&limit=100"
ROOT = pathlib.Path(__file__).resolve().parent

def main():
    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "ProjectOutlierResearch/0.2"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)

    markets = payload.get("markets", [])
    if not isinstance(markets, list):
        raise ValueError("Invalid market data response")

    results = []
    for market in markets:
        results.append({
            "ticker": market.get("ticker"),
            "title": market.get("title"),
            "status": market.get("status"),
            "yes_bid_dollars": market.get("yes_bid_dollars"),
            "no_bid_dollars": market.get("no_bid_dollars"),
            "close_time": market.get("close_time"),
        })

    output = {
        "source": "Kalshi public API",
        "collected_at_utc": dt.datetime.now(
            dt.timezone.utc
        ).isoformat(),
        "market_count": len(results),
        "markets": results,
        "research_only": True,
    }

    folder = ROOT / "reports"
    folder.mkdir(exist_ok=True)
    destination = folder / "live_markets.json"
    destination.write_text(json.dumps(output, indent=2))
    print(f"Collected {len(results)} real market records")
    print(f"Saved to {destination}")

if __name__ == "__main__":
    main()
