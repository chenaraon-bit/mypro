"""Shadow mode: generate orders but do not execute.

Useful before canary/live rollout.
"""

import argparse
import pandas as pd

from ctrader.strategies.mean_reversion import make_signal


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--window", type=int, default=50)
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.set_index("timestamp").sort_index()

    sig = make_signal(window=args.window)(df).shift(1).fillna(0)

    prev = 0
    planned = []
    for ts, val in sig.items():
        cur = int(val)
        if cur != prev:
            side = "BUY" if cur > prev else "SELL"
            planned.append({"ts": str(ts), "symbol": args.symbol, "side": side, "note": "shadow-only"})
            prev = cur

    print({"planned_orders": len(planned)})
    for row in planned[:20]:
        print(row)


if __name__ == "__main__":
    main()
