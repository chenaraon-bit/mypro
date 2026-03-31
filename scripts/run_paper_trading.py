"""Replay CSV bars into a local paper account.

Example:
PYTHONPATH=src python scripts/run_paper_trading.py --csv your_ohlcv.csv --symbol BTCUSDT
"""

import argparse
import pandas as pd

from ctrader.execution.paper import PaperBroker
from ctrader.strategies.mean_reversion import make_signal


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--qty", type=float, default=0.001)
    ap.add_argument("--window", type=int, default=50)
    ap.add_argument("--start-cash", type=float, default=10000)
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.set_index("timestamp").sort_index()

    signal = make_signal(window=args.window)(df)
    target = signal.shift(1).fillna(0)

    broker = PaperBroker(starting_cash=args.start_cash)
    pos = 0
    for ts, row in df.iterrows():
        tgt = int(target.loc[ts])
        if tgt != pos:
            side = "BUY" if tgt > pos else "SELL"
            broker.place_market_order(str(ts), args.symbol, side, args.qty, float(row.open))
            pos = tgt

    eq = broker.equity({args.symbol: float(df.iloc[-1].close)})
    print({
        "cash": round(broker.cash, 4),
        "realized_pnl": round(broker.realized_pnl, 4),
        "position": broker.positions.get(args.symbol, 0.0),
        "equity": round(eq, 4),
        "fills": len(broker.fills),
    })


if __name__ == "__main__":
    main()
