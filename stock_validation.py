"""Conservative follow-up validation for Project Outlier stock signals.

A completed daily close triggers an entry at the NEXT day's open.
Train/test split is chronological. No parameter optimization or trading.
"""
import statistics

COST = 0.002
HOLD_DAYS = 5
STRATEGIES = ("oversold_rebound", "momentum_breakout")


def validate(rows, events, train_fraction=0.7):
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between zero and one")
    split = int(len(rows) * train_fraction)
    output = {"split_index": split, "split_date": rows[split]["date"],
              "entry": "next_session_open", "exit": "fifth_session_close",
              "assumed_roundtrip_cost": COST, "strategies": {}}
    for strategy in STRATEGIES:
        qualified = []
        for event in events:
            i = event["index"]
            exit_index = i + HOLD_DAYS
            if event["strategy"] != strategy or exit_index >= len(rows):
                continue
            entry = rows[i + 1].get("open")
            exit_price = rows[exit_index].get("close")
            if entry is None or exit_price is None or entry <= 0:
                continue
            # Partition by signal and exit to prevent a trade straddling the split.
            period = "train" if exit_index < split else ("test" if i >= split else "excluded_boundary")
            qualified.append({"index": i, "period": period,
                              "net_return": exit_price / entry - 1 - COST,
                              "baseline_return": exit_price / rows[i + 1]["close"] - 1 - COST})
        result = {}
        for period in ("train", "test"):
            selected = []
            next_eligible = -1
            for event in qualified:
                if event["period"] == period and event["index"] >= next_eligible:
                    selected.append(event)
                    next_eligible = event["index"] + HOLD_DAYS
            values = [e["net_return"] for e in selected]
            result[period] = {
                "sample_count": len(values),
                "average_net_return": round(statistics.mean(values), 6) if values else None,
                "median_net_return": round(statistics.median(values), 6) if values else None,
                "win_rate": round(sum(v > 0 for v in values) / len(values), 4) if values else None,
                "worst_trade": round(min(values), 6) if values else None,
                "best_trade": round(max(values), 6) if values else None,
                "minimum_20_samples_met": len(values) >= 20,
            }
        output["strategies"][strategy] = result
    return output
