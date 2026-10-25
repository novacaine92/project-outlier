"""Project Outlier stocks v0.1: read-only historical signal research.

Uses Stooq daily CSV as an unauthenticated *research* source. Missing data is
reported, never replaced with invented prices. No orders or brokerage access.
"""
import csv
import datetime as dt
import io
import json
import math
import pathlib
import statistics
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
TICKERS = ("AAPL", "MSFT", "NVDA", "AMD", "MU", "SPY", "QQQ", "XLI", "JPM", "CAT")
LOOKBACK = 20
HORIZON = 5
ROUNDTRIP_COST = 0.002  # illustrative 20 basis points, not a broker quote


def fetch_history(ticker):
    symbol = ticker.lower() + ".us"
    url = "https://stooq.com/q/d/l/?" + urllib.parse.urlencode({"s": symbol, "i": "d"})
    request = urllib.request.Request(url, headers={"User-Agent": "ProjectOutlierResearch/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8-sig")
    rows = []
    for row in csv.DictReader(io.StringIO(body)):
        try:
            day = dt.date.fromisoformat(row["Date"])
            close = float(row["Close"])
            volume = float(row["Volume"])
            if math.isfinite(close) and close > 0 and math.isfinite(volume) and volume >= 0:
                rows.append({"date": day.isoformat(), "close": close, "volume": volume})
        except (KeyError, ValueError, TypeError):
            continue
    return sorted({r["date"]: r for r in rows}.values(), key=lambda r: r["date"])


def signals(rows):
    """Generate signals from past and current daily bars, never future bars."""
    found = []
    for i in range(LOOKBACK, len(rows) - HORIZON):
        prior = rows[i - LOOKBACK:i]
        current = rows[i]
        prices = [r["close"] for r in prior]
        mean = statistics.mean(prices)
        stdev = statistics.pstdev(prices)
        if stdev <= 0:
            continue
        z = (current["close"] - mean) / stdev
        average_volume = statistics.mean(r["volume"] for r in prior)
        volume_ratio = current["volume"] / average_volume if average_volume > 0 else 0
        strategies = []
        if z <= -2:
            strategies.append("oversold_rebound")
        if current["close"] > max(prices) and volume_ratio >= 1.5:
            strategies.append("momentum_breakout")
        for strategy in strategies:
            future = rows[i + HORIZON]["close"]
            gross = future / current["close"] - 1
            found.append({
                "date": current["date"], "index": i, "strategy": strategy,
                "close": round(current["close"], 4),
                "z_score": round(z, 3), "volume_ratio": round(volume_ratio, 3),
                "forward_5d_gross_return": round(gross, 6),
                "forward_5d_net_return": round(gross - ROUNDTRIP_COST, 6),
            })
    return found


def summarize(events):
    """Non-overlapping events within each strategy; no overlapping 5-day holds."""
    summary = {}
    for strategy in ("oversold_rebound", "momentum_breakout"):
        selected = []
        last = -HORIZON - 1
        for event in events:
            if event["strategy"] == strategy and event["index"] >= last + HORIZON:
                selected.append(event)
                last = event["index"]
        returns = [e["forward_5d_net_return"] for e in selected]
        summary[strategy] = {
            "nonoverlapping_samples": len(returns),
            "average_net_return": round(statistics.mean(returns), 6) if returns else None,
            "win_rate": round(sum(r > 0 for r in returns) / len(returns), 4) if returns else None,
            "last_signal_date": selected[-1]["date"] if selected else None,
        }
    return summary


def main():
    output = {
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "data_source": "Stooq daily historical CSV; availability and adjustments not guaranteed",
        "research_only": True,
        "assumed_roundtrip_cost": ROUNDTRIP_COST,
        "holding_period_trading_days": HORIZON,
        "limitations": [
            "Retrospective signals are not forward-tested or statistically validated",
            "Historical prices may be adjusted; dividends and corporate actions need verification",
            "Trading at the signal day's close may be impossible after observing the closing bar",
            "No bid/ask, actual fill, tax, shorting, or market-impact modeling",
            "Small samples and multiple testing can create spurious performance",
        ],
        "symbols": {},
    }
    for ticker in TICKERS:
        try:
            bars = fetch_history(ticker)
            if len(bars) < LOOKBACK + HORIZON + 1:
                output["symbols"][ticker] = {"status": "insufficient_history", "bars": len(bars)}
                continue
            events = signals(bars)
            output["symbols"][ticker] = {
                "status": "ok", "bars": len(bars), "last_bar_date": bars[-1]["date"],
                "last_close": bars[-1]["close"], "summary": summarize(events),
                "recent_historical_signals": [
                    {k: v for k, v in e.items() if k != "index"} for e in events[-5:]
                ],
            }
        except Exception as exc:
            output["symbols"][ticker] = {"status": "data_error", "error_type": type(exc).__name__}
    folder = ROOT / "reports"
    folder.mkdir(exist_ok=True)
    (folder / "stock_research.json").write_text(json.dumps(output, indent=2))
    lines = ["# Project Outlier | Stock research v0.1", "",
             "Research only. Historical exploratory signals are **not** investment recommendations.",
             "", "| Ticker | Bars | Oversold samples | Oversold mean net | Momentum samples | Momentum mean net |",
             "|---|---:|---:|---:|---:|---:|"]
    for ticker, item in output["symbols"].items():
        if item["status"] != "ok":
            lines.append(f"| {ticker} | {item['status']} | | | | |")
            continue
        a, b = item["summary"]["oversold_rebound"], item["summary"]["momentum_breakout"]
        def fmt(value):
            return f"{value:.2%}" if value is not None else "N/A"
        lines.append(f"| {ticker} | {item['bars']} | {a['nonoverlapping_samples']} | {fmt(a['average_net_return'])} | {b['nonoverlapping_samples']} | {fmt(b['average_net_return'])} |")
    lines += ["", "Signal-day close is used as a hypothetical entry, which can introduce execution bias.",
              "Historical returns are not proof of a repeatable edge. See JSON for caveats.", ""]
    (folder / "stock_research.md").write_text("\n".join(lines))
    print("Stock research complete:", {k: v["status"] for k, v in output["symbols"].items()})


if __name__ == "__main__":
    main()
